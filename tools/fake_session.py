"""Genera fixtures/session_01.dj sin cámara: el tablero de board_spec.json visto
por una cámara sintética a 0,6 m con 40° de inclinación, que oscila un poco.

    python tools/fake_session.py

Los cuadros son realistas (el tablero dibujado con sus marcadores ArUco), así
que también sirven para probar la detección. La pose del header es la verdadera.
"""
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dejarik.board import ROOT, load_spec, render_board  # noqa: E402
from dejarik.protocol import encode_frame  # noqa: E402
from dejarik.recording import Recorder  # noqa: E402
from dejarik.vision import to_view_matrix  # noqa: E402

W, H = 1280, 720
K = np.array([[900.0, 0, 640], [0, 900.0, 360], [0, 0, 1]])
FPS = 30
FRAMES = 90  # 3 s; la oscilación tiene período 3 s, así el loop no salta


def synthetic_pose(phase, distance=0.6, tilt_deg=40.0):
    """Pose tablero->cámara (rvec, tvec) de OpenCV. phase en [0, 1)."""
    s = math.sin(2 * math.pi * phase)
    look_down = np.diag([1.0, -1.0, -1.0])  # cámara arriba mirando hacia abajo
    tilt, _ = cv2.Rodrigues(np.array([math.radians(tilt_deg + 2 * s), 0, 0]))
    yaw, _ = cv2.Rodrigues(np.array([0, 0, math.radians(3 * s)]))
    R = tilt @ look_down @ yaw
    t = np.array([0.01 * s, 0.0, distance])
    rvec, _ = cv2.Rodrigues(R)
    return rvec.ravel(), t


def render_frame(board_img, A, rvec, tvec):
    """Proyecta la imagen del tablero con H = K [r1 r2 t] sobre un fondo gris."""
    R, _ = cv2.Rodrigues(rvec)
    Hb = K @ np.column_stack([R[:, 0], R[:, 1], tvec])
    frame = cv2.warpPerspective(board_img, Hb @ A, (W, H), flags=cv2.INTER_LINEAR, borderValue=(90, 90, 90))
    return frame


def main(path=ROOT / "fixtures" / "session_01.dj"):
    spec = load_spec()
    board_img, A = render_board(spec, ppm=4000)
    path.parent.mkdir(exist_ok=True)
    with Recorder(path) as rec:
        for i in range(FRAMES):
            rvec, tvec = synthetic_pose(i / FRAMES)
            frame = render_frame(board_img, A, rvec, tvec)
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            pose = {"ok": True, "T": to_view_matrix(rvec, tvec), "n_markers": 12, "reproj_px": 0.0, "locked": False}
            hand = {"cell": None, "pinch": False, "px": None}
            data = encode_frame(i, round(i * 1000 / FPS), jpeg.tobytes(), pose,
                                [K[0, 0], K[1, 1], K[0, 2], K[1, 2]], [W, H], hand)
            rec.write(data, 1000 / FPS)
    print(f"-> {path} ({path.stat().st_size / 1e6:.1f} MB, {FRAMES} cuadros)")


if __name__ == "__main__":
    main()
