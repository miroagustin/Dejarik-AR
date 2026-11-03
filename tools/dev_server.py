"""Servidor de desarrollo para web/ mientras no existan transport.py y game.py.

    python tools/dev_server.py [fixtures/session_01.dj] [--autoplay]
    -> abrir http://127.0.0.1:8000/?p=0

Sirve web/ y board_spec.json, reproduce en loop los cuadros de un .dj y, en vez
de reglas reales, avanza una partida guionada con cada clic (mover, atacar,
golpe, contragolpe, muerte). R reinicia. --autoplay avanza solo cada 2 s. Sirve para probar el render, las
animaciones y el HUD sin cámara ni juego. Se borra cuando transport.py exista.
"""
import asyncio
import copy
import json
import mimetypes
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from websockets.asyncio.server import broadcast, serve
from websockets.datastructures import Headers
from websockets.http11 import Response

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
sys.path.insert(0, str(ROOT))
from dejarik.recording import read_dj  # noqa: E402

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("model/gltf-binary", ".glb")

KINDS = ["guardian", "bestia", "acechador", "soldado"]
HP = {"guardian": 3, "bestia": 2, "acechador": 2, "soldado": 2}
START = {0: [23, 24, 13, 14], 1: [17, 18, 19, 20]}


def initial_pieces():
    return [{"id": owner * 4 + i, "owner": owner, "kind": k, "cell": START[owner][i], "hp": HP[k], "alive": True}
            for owner in (0, 1) for i, k in enumerate(KINDS)]


# Guion: (turno que juega, pieza seleccionada, casillas legales, eventos sin id).
# La bestia azul (1) y la roja (5) se encuentran en el centro y pelean.
SCRIPT = [
    (0, 1, [12], [{"kind": "move", "piece": 1, "from": 24, "to": 12}]),
    (1, 5, [6], [{"kind": "move", "piece": 5, "from": 18, "to": 6}]),
    (0, 1, [0, 11], [{"kind": "move", "piece": 1, "from": 12, "to": 0}]),
    (1, 5, [0, 5, 7], [{"kind": "attack", "piece": 5, "to": 0, "result": {"atk_roll": 5, "def_roll": 2, "outcome": "hit"}},
                       {"kind": "hit", "piece": 1, "result": {"hp": 1}}]),
    (0, 1, [6], [{"kind": "attack", "piece": 1, "to": 6, "result": {"atk_roll": 4, "def_roll": 1, "outcome": "hit"}},
                 {"kind": "hit", "piece": 5, "result": {"hp": 1}}]),
    (1, 5, [0], [{"kind": "attack", "piece": 5, "to": 0, "result": {"atk_roll": 1, "def_roll": 6, "outcome": "counter"}},
                 {"kind": "hit", "piece": 5, "result": {"hp": 0}},
                 {"kind": "death", "piece": 5, "from": 6}]),
]


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pieces, self.step, self.selected, self.turn, self.next_id = initial_pieces(), 0, None, 0, 1

    def state(self):
        cur = SCRIPT[self.step] if self.step < len(SCRIPT) else None
        legal = cur[2] if cur and self.selected is not None else []
        return {"v": 1, "type": "state", "turn": self.turn, "phase": "target" if self.selected is not None else "select",
                "pieces": self.pieces, "selected": self.selected, "legal": legal, "winner": None}

    def click(self):
        """Primer clic: selecciona. Segundo clic: ejecuta el paso. -> eventos (o [])."""
        if self.step >= len(SCRIPT):
            self.reset()
            return []
        turn, piece, _, evs = SCRIPT[self.step]
        if self.selected is None:
            self.selected = piece
            return []
        events = []
        for e in copy.deepcopy(evs):
            e["id"] = self.next_id
            self.next_id += 1
            events.append(e)
            p = next((q for q in self.pieces if q["id"] == e["piece"]), None)
            if e["kind"] == "move":
                p["cell"] = e["to"]
            elif e["kind"] == "hit":
                p["hp"] = e["result"]["hp"]
            elif e["kind"] == "death":
                p["alive"] = False
        self.turn = 1 - turn
        events.append({"id": self.next_id, "kind": "turn", "result": {"turn": self.turn}})
        self.next_id += 1
        self.selected = None
        self.step += 1
        return events


def serve_static(connection, request):
    path = unquote(urlsplit(request.path).path)
    if path == "/ws":
        return None
    if path == "/board_spec.json":
        f = ROOT / "board_spec.json"
    else:
        f = (WEB / (path.lstrip("/") or "index.html")).resolve()
        if not f.is_relative_to(WEB):
            f = None
    if f is None or not f.is_file():
        return connection.respond(404, "no existe\n")
    ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
    return Response(200, "OK", Headers([("Content-Type", ctype), ("Cache-Control", "no-store")]), f.read_bytes())


async def main(dj_path, autoplay=False):
    game, clients = Game(), set()
    frames = list(read_dj(dj_path))

    async def handler(ws):
        clients.add(ws)
        await ws.send(json.dumps({"v": 1, "type": "hello", "you": 0, "mode": "local", "remote": None}))
        await ws.send(json.dumps(game.state()))
        try:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "click":
                    events = game.click()
                    if events:
                        broadcast(clients, json.dumps({"v": 1, "type": "events", "events": events}))
                    broadcast(clients, json.dumps(game.state()))
                elif msg.get("type") == "key" and msg.get("key") == "reset":
                    game.reset()
                    broadcast(clients, json.dumps(game.state()))
        finally:
            clients.discard(ws)

    async def pump_frames():
        i = 0
        while True:
            dt, data = frames[i % len(frames)]
            broadcast(clients, data)
            i += 1
            await asyncio.sleep(dt / 1000)

    async def autoplayer():
        while True:
            await asyncio.sleep(2)
            events = game.click()
            if events:
                broadcast(clients, json.dumps({"v": 1, "type": "events", "events": events}))
            broadcast(clients, json.dumps(game.state()))

    async with serve(handler, "127.0.0.1", 8000, process_request=serve_static, max_size=1024):
        print("http://127.0.0.1:8000/?p=0  (Ctrl+C para salir)")
        if autoplay:
            asyncio.create_task(autoplayer())
        await pump_frames()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--autoplay"]
    asyncio.run(main(args[0] if args else ROOT / "fixtures" / "session_01.dj", "--autoplay" in sys.argv))
