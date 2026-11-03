"""Formato .dj: JSONL, una línea por cuadro que sale hacia el anfitrión,
{"dt_ms": int, "data": base64(header + JPEG)}. No guarda state ni events.

Días 1–2: escribir y leer (los usa tools/fake_session.py). replay() llega en
los días 6–10.
"""
import base64
import json


class Recorder:
    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")

    def write(self, data, dt_ms):
        self.f.write(json.dumps({"dt_ms": int(dt_ms), "data": base64.b64encode(data).decode("ascii")}) + "\n")

    def close(self):
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def read_dj(path):
    """-> iterador de (dt_ms, bytes del cuadro)."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                yield rec["dt_ms"], base64.b64decode(rec["data"])
