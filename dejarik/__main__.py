"""python -m dejarik [--mode cpu|local|remote] [--input mouse|hand|both] [--replay X.dj]
                   [--record X.dj] [--resume] [--no-browser]

Levanta la cámara (o el replay), la mano, el servidor y Chrome en una ventana --app.
"""
import argparse
import asyncio
import secrets
import subprocess
import threading

import numpy as np

from dejarik import tunnel
from dejarik.board import ROOT, load_spec
from dejarik.config import CALIB_PATH, load_calib, load_config
from dejarik.transport import SAVE_PATH, LatestBox, Server, load_state
from dejarik.vision import Flags

TOKEN_PATH = ROOT / "save" / "host_token"
CHROME_FLAGS = ["--disable-features=CalculateNativeWinOcclusion", "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows", "--autoplay-policy=no-user-gesture-required"]


def parse_args(argv=None):
    ap = argparse.ArgumentParser(prog="python -m dejarik")
    ap.add_argument("--mode", choices=["cpu", "local", "remote"], default="cpu")
    ap.add_argument("--input", choices=["mouse", "hand", "both"], default="both")
    ap.add_argument("--replay", metavar="X.dj")
    ap.add_argument("--record", metavar="X.dj")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    return ap.parse_args(argv)


def camera_K(cam):
    size = (cam["width"], cam["height"])
    if CALIB_PATH.exists():
        K, dist, _ = load_calib(size)
        return K, dist
    # ponytail: sin calib.npz, fx = 0,625·ancho (ajustado contra el tablero con la webcam de la notebook).
    print("AVISO: no hay calib.npz (correr tools/calibrate.py); uso una K aproximada")
    f = 0.625 * size[0]
    return np.array([[f, 0, size[0] / 2], [0, f, size[1] / 2], [0, 0, 1]]), np.zeros(5)


def host_token(resume):
    if resume and TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()
    tok = secrets.token_urlsafe(16)
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    TOKEN_PATH.write_text(tok)
    return tok


def open_browser(chrome_path, url):
    profile = ROOT / "save" / "chrome"  # perfil propio: si Chrome ya está abierto, ignoraría los flags
    try:
        subprocess.Popen([chrome_path, f"--app={url}", f"--user-data-dir={profile}", *CHROME_FLAGS])
    except OSError as e:
        print(f"No se pudo abrir el navegador ({chrome_path}): {e}\nAbrir a mano: {url}")


def main(argv=None):
    args = parse_args(argv)
    cfg, spec = load_config(), load_spec()
    port = cfg["net"]["port"]
    flags, stop = Flags(), threading.Event()
    htok, rtok = host_token(args.resume), secrets.token_urlsafe(16)

    state = load_state() if args.resume and SAVE_PATH.exists() else None
    recorder = None
    if args.record:
        from dejarik.recording import Recorder
        recorder = Recorder(args.record)

    remote_url = None
    if args.mode == "remote":
        url = tunnel.start(port, cfg["net"]["cloudflared_path"])
        if url:
            remote_url = f"{url}/?p=1&k={rtok}"
            print(f"\nLink para el jugador remoto:\n  {remote_url}\n")
        else:
            print("Túnel no disponible: se puede seguir en local o cpu (tecla P).")

    server = Server(cfg, spec, flags, mode=args.mode, host_token=htok, remote_token=rtok, remote_url=remote_url,
                    allow_remote=args.mode == "remote", tunnel_alive=tunnel.alive, input_mode=args.input,
                    state=state, recorder=recorder)

    cap = None
    if args.replay:
        from dejarik.recording import replay
        threading.Thread(target=replay, args=(args.replay, server.publish, flags, stop, cfg["net"]),
                         daemon=True).start()
    else:
        from dejarik.vision import PoseEstimator, open_camera, vision_loop
        K, dist = camera_K(cfg["camera"])
        cap = open_camera(cfg["camera"])
        hands_box = LatestBox()
        threading.Thread(target=vision_loop, daemon=True,
                         args=(cap, PoseEstimator(spec, K, dist, cfg), server.publish, flags, stop, cfg["net"]),
                         kwargs={"get_hand": hands_box.get}).start()
        if args.input != "mouse":
            from dejarik.hands import hands_loop

            def on_tap(cell):
                server.loop.call_soon_threadsafe(server.on_host_tap, cell)
            threading.Thread(target=hands_loop, daemon=True,
                             args=(server.bus.get, hands_box.put, on_tap, stop, K, dist, spec,
                                   cfg["hands"])).start()

    host_url = f"http://127.0.0.1:{port}/?p=0&k={htok}"

    async def run():
        started = asyncio.get_running_loop().create_future()
        task = asyncio.create_task(server.run(port, started))
        await started
        if args.no_browser:  # el host_token nunca se imprime: queda en save/host_token
            print(f"Anfitrión: http://127.0.0.1:{port}/?p=0&k=<contenido de save/host_token>")
        if not args.no_browser:
            if args.resume:
                await asyncio.sleep(3)  # la ventana que ya estaba abierta se reconecta sola
            if not server._hosts():
                open_browser(cfg["browser"]["chrome_path"], host_url)
        await task

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        tunnel.stop()
        if recorder:
            recorder.close()
        if cap:
            cap.release()


if __name__ == "__main__":
    main()
