"""Calibra la webcam de la demo con el damero de print/checker.pdf (9x6 esquinas).

    python tools/calibrate.py            # damero (print/checker.pdf, A4)
    python tools/calibrate.py --tablero  # el tablero del juego: sus 12 marcadores ArUco

Con --tablero cada vista necesita al menos 8 marcadores; inclinar la hoja hacia
distintos lados (o mover la notebook) entre captura y captura.

ESPACIO: captura una vista (solo si encuentra el damero). C: calibra y guarda
calib.npz. Q: salir. Mover el damero por toda la imagen y con distintas
inclinaciones. Usar la misma cámara, resolución y foco que en la demo.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dejarik.board import aruco_board, dictionary, load_spec  # noqa: E402
from dejarik.config import CALIB_PATH, load_config  # noqa: E402
from dejarik.vision import open_camera  # noqa: E402

PATTERN = (9, 6)
MIN_VIEWS = 15
MAX_RMS = 0.5
MAX_RMS_BOARD = 1.0  # las esquinas de marcadores ArUco chicos son menos precisas que las del damero

# El tamaño del cuadrado no cambia K, así que se usa 1 como unidad.
OBJ = np.zeros((PATTERN[0] * PATTERN[1], 3), np.float32)
OBJ[:, :2] = np.mgrid[0:PATTERN[0], 0:PATTERN[1]].T.reshape(-1, 2)


def board_finder():
    """-> find(gray) -> (encontrado, puntos 3D, puntos de imagen, para dibujar)."""
    spec = load_spec()
    board = aruco_board(spec)
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    det = cv2.aruco.ArucoDetector(dictionary(spec), params)

    def find(gray):
        corners, ids, _ = det.detectMarkers(gray)
        if ids is None or len(ids) < 8:
            return False, None, None, (corners, ids)
        obj, img = board.matchImagePoints(corners, ids)
        return True, obj, img, (corners, ids)
    return find


def checker_find(gray):
    found, corners = cv2.findChessboardCornersSB(gray, PATTERN)
    return found, OBJ, corners, corners


def main():
    use_board = "--tablero" in sys.argv
    find = board_finder() if use_board else checker_find
    cap = open_camera(load_config()["camera"])
    views, objs, size = [], [], None
    while True:
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("La cámara no devolvió imagen")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        size = gray.shape[::-1]
        found, obj, corners, draw = find(gray)
        show = frame.copy()
        if use_board and draw[1] is not None:
            cv2.aruco.drawDetectedMarkers(show, draw[0], draw[1])
        elif found:
            cv2.drawChessboardCorners(show, PATTERN, corners, found)
        cv2.putText(show, f"vistas: {len(views)}/{MIN_VIEWS}  {size[0]}x{size[1]}  [ESPACIO] capturar [C] calibrar [Q] salir",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if found else (0, 0, 255), 2)
        cv2.imshow("calibrar", show)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" ") and found:
            views.append(corners)
            objs.append(obj)
        elif key in (ord("c"), ord("C")):
            if len(views) < MIN_VIEWS:
                print(f"Faltan vistas: {len(views)}/{MIN_VIEWS}")
                continue
            if use_board:
                # Un plano visto desde pocas inclinaciones deja libres fx/fy y el centro, y la
                # optimización los usa para compensar (daba fx 700, fy 500, cy 235). Se fija lo
                # que una webcam ya cumple: pixel cuadrado, centro en la mitad, sin tangencial.
                flags = (cv2.CALIB_FIX_ASPECT_RATIO | cv2.CALIB_FIX_PRINCIPAL_POINT
                         | cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K3)
                rms, K, dist, _, _ = cv2.calibrateCamera(objs, views, size, np.eye(3), None, flags=flags)
            else:
                rms, K, dist, _, _ = cv2.calibrateCamera(objs, views, size, None, None)
            print(f"RMS = {rms:.3f} px\nK =\n{K}\ndist = {dist.ravel()}")
            max_rms = MAX_RMS_BOARD if use_board else MAX_RMS
            if rms >= max_rms:
                print(f"RMS >= {max_rms}: no se guarda. Repetir con vistas nítidas (sin mover la hoja al capturar).")
                views.clear()
                objs.clear()
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
