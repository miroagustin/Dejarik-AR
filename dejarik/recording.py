"""Formato .dj: JSONL, una línea por cuadro que sale hacia el anfitrión,
{"dt_ms": int, "data": base64(header + JPEG)}. No guarda state ni events.
"""
import base64
import json
import time


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


def replay(path, publish, flags, stop, net_cfg):
    """Reproduce un .dj en loop respetando dt_ms y publica paquetes con la misma forma
    que vision_loop. game corre en vivo; no hay hilo de manos."""
    import cv2
    import numpy as np

    from dejarik.protocol import decode_frame, encode_frame
    from dejarik.vision import Pose, encode_remote
    frames = list(read_dj(path))
    frame_id = 0
    while not stop.is_set():
        for dt_ms, data in frames:
            if stop.is_set():
                return
            header, jpeg = decode_frame(data)
            header["frame_id"] = frame_id  # crece siempre, aunque el archivo vuelva a empezar
            header.pop("debug", None)
            remote_msg = None
            if flags.remote_connected.is_set():
                bgr = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                remote_msg = encode_remote(frame_id, header["t"], bgr, header["pose"], header["K"],
                                           header["hand"], net_cfg)
            host_msg = encode_frame(frame_id, header["t"], jpeg, header["pose"], header["K"], header["size"],
                                    header["hand"])
            publish({"frame_id": frame_id, "t": time.monotonic(), "bgr": None, "host_msg": host_msg,
                     "remote_msg": remote_msg, "pose": Pose(ok=header["pose"]["ok"])})
            frame_id += 1
            time.sleep(dt_ms / 1000)
