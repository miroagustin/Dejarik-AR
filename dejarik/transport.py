"""Servidor único en 127.0.0.1:8000: archivos de web/ en / y el WebSocket en /ws.

Es el dueño del juego: recibe clics, pinch y teclas, controla rol, turno y modo,
bloquea la entrada mientras hay animaciones sin confirmar, mueve al rival
automático y manda cuadros, estado y eventos a cada conexión.
"""
import asyncio
import mimetypes
import os
import random
import secrets
import threading
import time
from urllib.parse import parse_qs, unquote, urlsplit

from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Response

from dejarik import ai, game, protocol
from dejarik.board import ROOT, cell_at

WEB = ROOT / "web"
SAVE_PATH = ROOT / "save" / "state.json"
MODES = ("cpu", "local", "remote")

# En Windows el registro suele dar text/plain para .js y Chrome rechaza los módulos.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("model/gltf-binary", ".glb")


class LatestBox:
    """Lock + último valor. Se usa como frame_bus y como hands_box."""

    def __init__(self):
        self._lock, self._v = threading.Lock(), None

    def put(self, v):
        with self._lock:
            self._v = v

    def get(self):
        with self._lock:
            return self._v


def can_act(role, mode, turn):
    """role: host (p=0), remote (p=1) o ai. Tabla de "Modos de juego y jugadores"."""
    if role == "host":
        return mode == "local" or turn == 0
    if role == "remote":
        return mode == "remote" and turn == 1
    return role == "ai" and mode == "cpu" and turn == 1


def serve_static(connection, request):
    path = unquote(urlsplit(request.path).path)
    if path == "/ws":
        return None
    if path == "/board_spec.json":
        f = ROOT / "board_spec.json"
    else:
        f = (WEB / (path.lstrip("/") or "index.html")).resolve()
        if not f.is_relative_to(WEB.resolve()):
            f = None
    if f is None or not f.is_file():
        return connection.respond(404, "no existe\n")
    ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
    return Response(200, "OK", Headers([("Content-Type", ctype), ("Cache-Control", "no-store")]), f.read_bytes())


def save_state(state, path=SAVE_PATH):
    """Archivo temporal + os.replace, para que un corte no lo deje a medias."""
    path.parent.mkdir(exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(game.to_json(state), encoding="utf-8")
    os.replace(tmp, path)


def load_state(path=SAVE_PATH):
    return game.from_json(path.read_text(encoding="utf-8"))


class Server:
    def __init__(self, cfg, spec, flags, *, mode="cpu", host_token="", remote_token="", remote_url=None,
                 allow_remote=False, tunnel_alive=lambda: False, input_mode="both", state=None,
                 recorder=None, save_path=SAVE_PATH):
        self.cfg, self.spec, self.flags = cfg, spec, flags
        self.mode, self.allow_remote, self.tunnel_alive = mode, allow_remote, tunnel_alive
        self.host_token, self.remote_token, self.remote_url = host_token, remote_token, remote_url
        self.input_mode, self.recorder, self.save_path = input_mode, recorder, save_path
        self.state = state or game.new_game(cfg["game"]["seed"])
        self.bus = LatestBox()
        self.loop = None
        self.conns = {}          # ws -> {"role", "wake": asyncio.Event, "unacked": set()}
        self.remote_ws = None
        self.pending = set()     # ids de eventos sin anim_done
        self.anim_deadline = 0.0
        self.ai_task = None
        self._last_rec_t = None

    # ---- desde otros hilos ----

    def publish(self, pkt):
        """Hilo de visión o de replay: deja el paquete y despierta a las tareas de envío."""
        self.bus.put(pkt)
        if self.recorder:
            now = time.monotonic()
            self.recorder.write(pkt["host_msg"], 0 if self._last_rec_t is None else (now - self._last_rec_t) * 1000)
            self._last_rec_t = now
        if self.loop:
            self.loop.call_soon_threadsafe(self._wake_all)

    def _wake_all(self):
        for c in self.conns.values():
            c["wake"].set()

    # ---- envío ----

    def _send(self, ws, text):
        asyncio.ensure_future(self._safe_send(ws, text))

    @staticmethod
    async def _safe_send(ws, data):
        try:
            await ws.send(data)
        except Exception:  # la conexión se cerró en el medio; el handler la limpia
            pass

    def _broadcast(self, text):
        for ws in list(self.conns):
            self._send(ws, text)

    def _hosts(self):
        return [ws for ws, c in self.conns.items() if c["role"] == "host"]

    def _hello(self, ws):
        role = self.conns[ws]["role"]
        remote = None
        if role == "host" and self.allow_remote:
            tunnel = "up" if self.tunnel_alive() and self.remote_url else "down"
            remote = {"url": self.remote_url, "tunnel": tunnel, "connected": self.remote_ws is not None}
        self._send(ws, protocol.hello_msg(0 if role == "host" else 1, self.mode, remote))

    def _hello_all(self, hosts_only=False):
        for ws in (self._hosts() if hosts_only else list(self.conns)):
            self._hello(ws)

    def _state_msg(self):
        return protocol.state_msg(self.state, animating=bool(self.pending))

    async def _send_frames(self, ws, c):
        remote = c["role"] == "remote"
        min_dt = 1 / self.cfg["net"]["remote_max_fps"] if remote else 0
        last_id, last_t = None, 0.0
        while True:
            await c["wake"].wait()
            c["wake"].clear()
            pkt = self.bus.get()
            if pkt is None or pkt["frame_id"] == last_id:
                continue
            if remote:
                # cloudflared acepta todo y acumula: máximo 2 cuadros sin frame_ack.
                if pkt["remote_msg"] is None or len(c["unacked"]) >= 2 or time.monotonic() - last_t < min_dt:
                    continue
                c["unacked"].add(pkt["frame_id"])
                last_t = time.monotonic()
            last_id = pkt["frame_id"]
            await ws.send(pkt["remote_msg"] if remote else pkt["host_msg"])

    # ---- conexiones ----

    def _role(self, path):
        q = parse_qs(urlsplit(path).query)
        p, k = q.get("p", [""])[0], q.get("k", [""])[0].encode()
        if p == "0" and self.host_token and secrets.compare_digest(k, self.host_token.encode()):
            return "host"
        if p == "1" and self.remote_token and secrets.compare_digest(k, self.remote_token.encode()):
            return "remote"
        return None

    async def handler(self, ws):
        role = self._role(ws.request.path)
        if role is None:
            await ws.close(4401, "token inválido")
            return
        if role == "remote" and self.remote_ws is not None:
            await ws.close(4409, "ya hay un jugador 1")
            return
        c = {"role": role, "wake": asyncio.Event(), "unacked": set()}
        self.conns[ws] = c
        if role == "remote":
            self.remote_ws = ws
            self.flags.remote_connected.set()
            self._hello_all(hosts_only=True)
        self._hello(ws)
        self._send(ws, self._state_msg())
        sender = asyncio.create_task(self._send_frames(ws, c))
        try:
            async for raw in ws:
                msg = protocol.parse_client(raw) if isinstance(raw, str) else None
                if msg:
                    self.on_message(ws, role, msg)
        finally:
            sender.cancel()
            del self.conns[ws]
            if ws is self.remote_ws:
                self.remote_ws = None
                self.flags.remote_connected.clear()
                self._hello_all(hosts_only=True)

    def on_message(self, ws, role, msg):
        kind = msg["type"]
        if kind == "click":
            if role == "host" and self.input_mode == "hand":
                return
            self.tap(role, cell_at(msg["x"], msg["y"], self.spec), ws)
        elif kind == "anim_done" and role == "host":
            if msg["id"] in self.pending:
                self.pending.discard(msg["id"])
                self.anim_deadline = time.monotonic() + self.cfg["anim"]["anim_timeout_s"]
                if not self.pending:
                    self._animations_done()
        elif kind == "frame_ack" and role == "remote":
            self.conns[ws]["unacked"].discard(msg["frame_id"])
            self.conns[ws]["wake"].set()
        elif kind == "key" and role == "host":
            self.on_key(msg["key"])

    def on_key(self, key):
        if key == "debug":
            (self.flags.debug_on.clear if self.flags.debug_on.is_set() else self.flags.debug_on.set)()
        elif key == "lock":
            self.flags.lock_toggle.set()
        elif key == "reset":
            self._cancel_ai()
            self.pending.clear()
            self.state, _ = game.apply(self.state, ("reset",))
            save_state(self.state, self.save_path)
            self._broadcast(self._state_msg())
            self._maybe_ai()
        elif key == "mode":
            cycle = [m for m in MODES if m != "remote" or self.allow_remote]
            self.mode = cycle[(cycle.index(self.mode) + 1) % len(cycle)] if self.mode in cycle else "cpu"
            self._cancel_ai()
            self._hello_all()
            self._maybe_ai()

    # ---- juego ----

    def on_host_tap(self, cell):
        """Pinch de la mano (llega con call_soon_threadsafe): mismos controles que un clic del anfitrión."""
        self.tap("host", cell, None)

    def tap(self, role, cell, ws):
        pkt = self.bus.get()
        if pkt is None or not pkt["pose"].ok:
            return  # tracking perdido: se ignoran clics y pinch
        reason = "animating" if self.pending else None if can_act(role, self.mode, self.state.turn) else "not_your_turn"
        if reason:
            for target in ([ws] if ws else self._hosts()):
                self._send(target, protocol.denied_msg(reason))
            return
        self.apply(("tap", cell))

    def apply(self, action):
        self.state, events = game.apply(self.state, action)
        save_state(self.state, self.save_path)
        if events:
            self.pending |= {e["id"] for e in events}
            self.anim_deadline = time.monotonic() + self.cfg["anim"]["anim_timeout_s"]
            # Primero los eventos: así el navegador anima en vez de saltar al estado nuevo.
            self._broadcast(protocol.events_msg(events))
        self._broadcast(self._state_msg())
        self._maybe_ai()

    def _animations_done(self):
        self._broadcast(self._state_msg())
        self._maybe_ai()

    def _maybe_ai(self):
        if (self.loop and can_act("ai", self.mode, self.state.turn) and self.state.phase != "over"
                and not self.pending and (self.ai_task is None or self.ai_task.done())):
            self.ai_task = self.loop.create_task(self._ai_turn())

    def _cancel_ai(self):
        if self.ai_task and not self.ai_task.done():
            self.ai_task.cancel()

    async def _ai_turn(self):
        a = self.cfg["ai"]
        await asyncio.sleep(random.uniform(a["think_min_s"], a["think_max_s"]))  # que parezca que piensa
        for i, action in enumerate(ai.choose(self.state)):
            if i:
                await asyncio.sleep(a["tap_gap_s"])  # que se vea la selección
            if self.pending or not can_act("ai", self.mode, self.state.turn):
                return
            self.apply(action)

    async def _watchdog(self):
        """Timeout de anim_done (un navegador colgado no traba la partida) y estado del túnel."""
        last_tunnel, next_tunnel = None, 0.0
        while True:
            await asyncio.sleep(0.2)
            now = time.monotonic()
            if self.pending and now > self.anim_deadline:
                self.pending.clear()
                self._animations_done()
            if self.allow_remote and now >= next_tunnel:
                next_tunnel = now + 2
                alive = self.tunnel_alive()
                if alive != last_tunnel:
                    last_tunnel = alive
                    self._hello_all(hosts_only=True)

    async def run(self, port=8000, started=None):
        """Corre hasta que lo cancelen. started: asyncio.Future que recibe el server (tests)."""
        self.loop = asyncio.get_running_loop()
        async with serve(self.handler, "127.0.0.1", port, process_request=serve_static,
                         max_size=1024, compression=None) as server:
            watchdog = asyncio.create_task(self._watchdog())
            self._maybe_ai()
            if started:
                started.set_result(server)
            try:
                await asyncio.Future()
            finally:
                watchdog.cancel()
                self._cancel_ai()
