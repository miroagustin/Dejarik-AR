import asyncio
import copy
import json

import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from dejarik.board import load_spec
from dejarik.config import load_config
from dejarik.transport import Server, can_act
from dejarik.vision import Flags, Pose

HOST, REMOTE = "hosttok", "remotetok"


def test_can_act_table():
    expected = {("cpu", "host", 0): True, ("cpu", "host", 1): False, ("cpu", "remote", 0): False,
                ("cpu", "remote", 1): False, ("local", "host", 0): True, ("local", "host", 1): True,
                ("local", "remote", 0): False, ("local", "remote", 1): False, ("remote", "host", 0): True,
                ("remote", "host", 1): False, ("remote", "remote", 0): False, ("remote", "remote", 1): True}
    for (mode, role, turn), ok in expected.items():
        assert can_act(role, mode, turn) == ok, (mode, role, turn)
    assert can_act("ai", "cpu", 1) and not can_act("ai", "local", 1)


def run(coro_fn, tmp_path, cfg=None, **kw):
    """Levanta un Server en un puerto libre, corre coro_fn(server, url) y lo apaga."""
    async def main():
        server = Server(cfg or load_config(), load_spec(), Flags(), host_token=HOST, remote_token=REMOTE,
                        save_path=tmp_path / "state.json", **kw)
        started = asyncio.get_running_loop().create_future()
        task = asyncio.create_task(server.run(0, started))
        ws_server = await started
        port = ws_server.sockets[0].getsockname()[1]
        try:
            return await coro_fn(server, f"ws://127.0.0.1:{port}", port)
        finally:
            task.cancel()
    return asyncio.run(main())


def frame(i):
    return {"frame_id": i, "t": i, "bgr": None, "host_msg": b"h%d" % i, "remote_msg": b"r%d" % i, "pose": Pose(ok=True)}


async def close_code(url):
    async with connect(url) as ws:
        with pytest.raises(ConnectionClosed):
            while True:
                await asyncio.wait_for(ws.recv(), 2)
    return ws.close_code


def test_roles_and_tokens(tmp_path):
    async def body(server, base, port):
        assert await close_code(f"{base}/ws?p=0") == 4401
        assert await close_code(f"{base}/ws?p=0&k=mal") == 4401
        assert await close_code(f"{base}/ws?p=1&k=mal") == 4401
        async with connect(f"{base}/ws?p=1&k={REMOTE}") as first:
            hello = json.loads(await first.recv())
            assert hello["type"] == "hello" and hello["you"] == 1
            assert await close_code(f"{base}/ws?p=1&k={REMOTE}") == 4409
    run(body, tmp_path)


def test_no_path_traversal(tmp_path):
    async def body(server, base, port):
        out = []
        for path in ("/../dejarik/game.py", "/%2e%2e/dejarik/game.py", "/index.html"):
            r, w = await asyncio.open_connection("127.0.0.1", port)
            w.write(f"GET {path} HTTP/1.1\r\nHost: x\r\n\r\n".encode())
            out.append((await r.readline()).decode())
            w.close()
        return out
    a, b, ok = run(body, tmp_path)
    assert " 404 " in a and " 404 " in b and " 200 " in ok


def test_big_message_closes(tmp_path):
    async def body(server, base, port):
        async with connect(f"{base}/ws?p=0&k={HOST}") as ws:
            await ws.send(json.dumps({"v": 1, "type": "click", "x": 0, "y": 0, "pad": "x" * 2000}))
            with pytest.raises(ConnectionClosed):
                while True:
                    await asyncio.wait_for(ws.recv(), 2)
            return ws.close_code
    assert run(body, tmp_path) == 1009


def test_remote_stops_with_two_unacked(tmp_path):
    cfg = copy.deepcopy(load_config())
    cfg["net"]["remote_max_fps"] = 1000

    async def body(server, base, port):
        async with connect(f"{base}/ws?p=1&k={REMOTE}") as ws:
            await ws.recv(), await ws.recv()  # hello, state
            got = []
            for i in range(6):
                server.publish(frame(i))
                await asyncio.sleep(0.05)
            while True:
                try:
                    m = await asyncio.wait_for(ws.recv(), 0.3)
                except asyncio.TimeoutError:
                    break
                if isinstance(m, bytes):
                    got.append(m)
            assert got == [b"r0", b"r1"]
            await ws.send(json.dumps({"v": 1, "type": "frame_ack", "frame_id": 0}))
            assert await asyncio.wait_for(ws.recv(), 1) == b"r5"  # después del ack, el más nuevo
    run(body, tmp_path, cfg=cfg)


def test_mode_change_cancels_ai(tmp_path):
    cfg = copy.deepcopy(load_config())
    cfg["ai"].update(think_min_s=0.4, think_max_s=0.4)

    async def body(server, base, port):
        server.publish(frame(0))
        server.state.turn = 1
        before = copy.deepcopy(server.state)
        async with connect(f"{base}/ws?p=0&k={HOST}") as ws:
            server._maybe_ai()
            await asyncio.sleep(0.1)
            await ws.send(json.dumps({"v": 1, "type": "key", "key": "mode"}))
            await asyncio.sleep(1.5)
            assert server.mode == "local"
            assert server.state == before  # ningún tap de la PC
            assert not server.pending
    run(body, tmp_path, mode="cpu")


def test_cpu_plays_after_host_move(tmp_path):
    cfg = copy.deepcopy(load_config())
    cfg["ai"].update(think_min_s=0, think_max_s=0, tap_gap_s=0)

    async def body(server, base, port):
        server.publish(frame(0))
        async with connect(f"{base}/ws?p=0&k={HOST}") as ws:
            async def click(cell):
                from dejarik.board import cell_center
                x, y = cell_center(cell, server.spec)
                await ws.send(json.dumps({"v": 1, "type": "click", "x": x, "y": y}))
            await click(13)
            await click(1)            # acechador 13 -> 1
            events = []
            while len(events) < 4:    # move + turn del anfitrión, move + turn de la PC
                m = json.loads(await asyncio.wait_for(ws.recv(), 3))
                if m["type"] == "events":
                    events += m["events"]
                    for e in m["events"]:
                        await ws.send(json.dumps({"v": 1, "type": "anim_done", "id": e["id"]}))
                elif m["type"] == "denied":
                    raise AssertionError(m)
            assert [e["kind"] for e in events] == ["move", "turn", "move", "turn"]
            assert events[2]["piece"] >= 4 and server.state.turn == 0
    run(body, tmp_path, mode="cpu")
