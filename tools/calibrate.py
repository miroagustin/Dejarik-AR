"""Calibra la webcam de la demo con el damero de print/checker.pdf (9x6 esquinas).

    python tools/calibrate.py

ESPACIO: captura una vista (solo si encuentra el damero). C: calibra y guarda
calib.npz. Q: salir. Mover el damero por toda la imagen y con distintas
inclinaciones. Usar la misma cámara, resolución y foco que en la demo.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dejarik.config import CALIB_PATH, load_config  # noqa: E402
from dejarik.vision import open_camera  # noqa: E402

PATTERN = (9, 6)
MIN_VIEWS = 15
MAX_RMS = 0.5

# El tamaño del cuadrado no cambia K, así que se usa 1 como unidad.
OBJ = np.zeros((PATTERN[0] * PATTERN[1], 3), np.float32)
OBJ[:, :2] = np.mgrid[0:PATTERN[0], 0:PATTERN[1]].T.reshape(-1, 2)


def main():
    cap = open_camera(load_config()["camera"])
    views, size = [], None
    while True:
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("La cámara no devolvió imagen")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        size = gray.shape[::-1]
        found, corners = cv2.findChessboardCornersSB(gray, PATTERN)
        show = frame.copy()
        if found:
            cv2.drawChessboardCorners(show, PATTERN, corners, found)
        cv2.putText(show, f"vistas: {len(views)}/{MIN_VIEWS}  {size[0]}x{size[1]}  [ESPACIO] capturar [C] calibrar [Q] salir",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if found else (0, 0, 255), 2)
        cv2.imshow("calibrar", show)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" ") and found:
            views.append(corners)
        elif key in (ord("c"), ord("C")):
            if len(views) < MIN_VIEWS:
                print(f"Faltan vistas: {len(views)}/{MIN_VIEWS}")
                continue
            rms, K, dist, _, _ = cv2.calibrateCamera([OBJ] * len(views), views, size, None, None)
            print(f"RMS = {rms:.3f} px\nK =\n{K}\ndist = {dist.ravel()}")
            if rms >= MAX_RMS:
                print(f"RMS >= {MAX_RMS}: no se guarda. Sacar las vistas borrosas y repetir.")
                views.clear()
                continue
            np.savez(CALIB_PATH, K=K, dist=dist, size=np.array(size), rms=rms)
            print(f"-> {CALIB_PATH}")
            break
        elif key in (ord("q"), ord("Q")):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
