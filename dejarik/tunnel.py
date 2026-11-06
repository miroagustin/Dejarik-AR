"""Túnel rápido de cloudflared (modo remote): URL pública https://….trycloudflare.com
hacia 127.0.0.1:<port>, sin cuenta ni puertos abiertos.

Falla si existe %USERPROFILE%\\.cloudflared\\config.yml (el README lo avisa).
"""
import re
import subprocess
import threading

from dejarik.board import ROOT

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
LOG_PATH = ROOT / "recordings" / "cloudflared.log"

_proc = None


def start(port, cloudflared_path):
    """Lanza cloudflared y espera la URL hasta 20 s. -> URL o None."""
    global _proc
    exe = ROOT / cloudflared_path
    try:
        _proc = subprocess.Popen([str(exe), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
                                 stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="replace")
    except OSError as e:
        print(f"No se pudo lanzar cloudflared ({exe}): {e}")
        return None
    found, url = threading.Event(), [None]

    def pump(stream):
        # Hay que vaciar stderr toda la vida del proceso: si el buffer se llena, cloudflared se traba.
        LOG_PATH.parent.mkdir(exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as log:
            for line in stream:
                log.write(line)
                log.flush()
                m = URL_RE.search(line)
                if m and not found.is_set():
                    url[0] = m.group(0)
                    found.set()

    threading.Thread(target=pump, args=(_proc.stderr,), daemon=True).start()
    found.wait(20)
    return url[0]


def alive():
    return _proc is not None and _proc.poll() is None


def stop():
    if alive():
        _proc.terminate()
        try:
            _proc.wait(5)
        except subprocess.TimeoutExpired:
            _proc.kill()
