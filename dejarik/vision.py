"""Visión: cámara y pose del tablero.

Días 1–2: solo open_camera (la usa tools/calibrate.py) y to_view_matrix (la usa
tools/fake_session.py). PoseEstimator y vision_loop llegan en los días 3–5.
"""
import cv2
import numpy as np

# OpenCV (x der, y abajo, z adelante) -> Three.js (y arriba, z atrás).
# Único lugar del proyecto donde se hace esta conversión.
CV_TO_GL = np.diag([1.0, -1.0, -1.0, 1.0])

_PROPS = {  # clave de [camera] en config.toml -> propiedad de OpenCV
    "autofocus": cv2.CAP_PROP_AUTOFOCUS,
    "focus": cv2.CAP_PROP_FOCUS,
    "auto_exposure": cv2.CAP_PROP_AUTO_EXPOSURE,
    "exposure": cv2.CAP_PROP_EXPOSURE,
    "auto_wb": cv2.CAP_PROP_AUTO_WB,
    "wb": cv2.CAP_PROP_WB_TEMPERATURE,
}


def open_camera(cam_cfg):
    cap = cv2.VideoCapture(cam_cfg.get("index", 0), cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara {cam_cfg.get('index', 0)}")
    # FOURCC antes que el tamaño: si no, DSHOW cae a YUY2 con pocos fps.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cam_cfg.get("fourcc", "MJPG")))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg.get("width", 1280))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg.get("height", 720))
    for key, prop in _PROPS.items():
        if key in cam_cfg:
            cap.set(prop, float(cam_cfg[key]))
    return cap


def to_view_matrix(rvec, tvec):
    """Pose tablero->cámara de OpenCV -> matriz 4x4 para Three.js, en orden por
    columnas (lista de 16, lista para Matrix4.fromArray)."""
    T = np.eye(4)
    T[:3, :3], _ = cv2.Rodrigues(np.asarray(rvec, dtype=np.float64).reshape(3, 1))
    T[:3, 3] = np.asarray(tvec, dtype=np.float64).reshape(3)
    return (CV_TO_GL @ T).flatten(order="F").tolist()
