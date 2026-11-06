"""Visión: cámara y pose del tablero (ver "Visión: del cuadro a la pose" en el diseño)."""
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np

from dejarik.board import aruco_board, dictionary
from dejarik.hands import NO_HAND
from dejarik.one_euro import PoseFilter
from dejarik.protocol import encode_frame

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


@dataclass
class Pose:
    ok: bool = False
    rvec: np.ndarray = None
    tvec: np.ndarray = None
    n_markers: int = 0
    reproj_px: float = 0.0
    locked: bool = False
    raw: tuple = None  # (rvec, tvec) sin filtrar, para el debug
    corners: list = field(default_factory=list)  # solo con debug
    ids: list = field(default_factory=list)

    def to_msg(self):
        """El campo "pose" del header de frame (docs/protocol.md)."""
        T = to_view_matrix(self.rvec, self.tvec) if self.rvec is not None else [0.0] * 16
        return {"ok": self.ok, "T": T, "n_markers": self.n_markers,
                "reproj_px": round(float(self.reproj_px), 3), "locked": self.locked}


def _rot_angle_deg(rvec_a, rvec_b):
    Ra, _ = cv2.Rodrigues(np.asarray(rvec_a, dtype=np.float64).reshape(3, 1))
    Rb, _ = cv2.Rodrigues(np.asarray(rvec_b, dtype=np.float64).reshape(3, 1))
    d, _ = cv2.Rodrigues(Ra.T @ Rb)
    return float(np.degrees(np.linalg.norm(d)))


class PoseEstimator:
    """update(gray, t) -> Pose. cfg es config.toml entero (usa [pose] y [filter.*])."""

    def __init__(self, spec, K, dist, cfg):
        self.K, self.dist = np.asarray(K, dtype=np.float64), np.asarray(dist, dtype=np.float64)
        self.board = aruco_board(spec)
        params = cv2.aruco.DetectorParameters()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector = cv2.aruco.ArucoDetector(dictionary(spec), params)
        self.p = cfg["pose"]
        self.filter = PoseFilter(cfg["filter"]["t"], cfg["filter"]["r"])
        self.last = None        # última pose válida (filtrada)
        self.last_t = -1e9
        self.prev_rvec = None   # última rvec cruda, para elegir entre las dos soluciones de IPPE
        self.lock_wanted = False
        self.locked_pose = None
        self.window = deque()   # (t, rvec, tvec) crudos, para decidir el bloqueo

    def toggle_lock(self):
        self.lock_wanted = not self.lock_wanted
        self.locked_pose = None
        self.window.clear()

    def solve(self, corners, ids):
        """-> (rvec, tvec, reproj_px) crudos, o None."""
        obj, img = self.board.matchImagePoints(corners, ids)
        if obj is None or len(obj) < 8:
            return None
        n, rvecs, tvecs, errs = cv2.solvePnPGeneric(obj, img, self.K, self.dist, flags=cv2.SOLVEPNP_IPPE)
        if n == 0:
            return None
        errs = np.asarray(errs).ravel()
        order = list(np.argsort(errs))
        best = order[0]
        # Si las dos soluciones del plano dan casi el mismo error, gana la más parecida a la anterior.
        if n > 1 and self.prev_rvec is not None and errs[order[1]] - errs[best] < 0.2 * errs[order[1]]:
            best = min(order[:2], key=lambda i: _rot_angle_deg(self.prev_rvec, rvecs[i]))
        rvec, tvec = cv2.solvePnPRefineLM(obj, img, self.K, self.dist, rvecs[best].copy(), tvecs[best].copy())
        proj, _ = cv2.projectPoints(obj, rvec, tvec, self.K, self.dist)
        err = float(np.sqrt(np.mean(np.sum((proj.reshape(-1, 2) - img.reshape(-1, 2)) ** 2, axis=1))))
        return rvec.ravel(), tvec.ravel(), err

    def update(self, gray, t=None, debug=False):
        t = time.monotonic() if t is None else t
        corners, ids, _ = self.detector.detectMarkers(gray)
        n = 0 if ids is None else len(ids)
        sol = self.solve(corners, ids) if n >= self.p["min_markers"] else None
        if sol and sol[2] > self.p["max_reproj_px"]:
            sol = None

        if self.locked_pose is not None:
            pose = Pose(**{**self.locked_pose.__dict__, "n_markers": n})
        elif sol:
            rvec, tvec, err = sol
            self.prev_rvec = rvec
            fr, ft = self.filter(rvec, tvec, t)
            pose = Pose(True, fr, ft, n, err, False, (rvec, tvec))
            self.last, self.last_t = pose, t
            if self.lock_wanted:
                self._try_lock(t, rvec, tvec, pose)
        elif self.last is not None and t - self.last_t <= self.p["hold_ms"] / 1000:
            pose = Pose(True, self.last.rvec, self.last.tvec, n, self.last.reproj_px)
        else:
            self.filter.reset()  # al volver, que salte a la pose nueva en vez de deslizarse
            self.prev_rvec = None
            pose = Pose(False, None, None, n, 0.0)

        if debug and ids is not None:
            pose.corners = [c.reshape(4, 2).round(1).tolist() for c in corners]
            pose.ids = ids.ravel().tolist()
        return pose

    def _try_lock(self, t, rvec, tvec, pose):
        self.window.append((t, rvec, tvec))
        while self.window and t - self.window[0][0] > self.p["lock_stable_s"]:
            self.window.popleft()
        if t - self.window[0][0] < self.p["lock_stable_s"] * 0.9:
            return
        ts = np.array([w[2] for w in self.window])
        mean_r = np.mean([w[1] for w in self.window], axis=0)
        if (np.linalg.norm(ts - ts.mean(axis=0), axis=1).max() * 1000 <= self.p["lock_max_dt_mm"]
                and max(_rot_angle_deg(mean_r, w[1]) for w in self.window) <= self.p["lock_max_drot_deg"]):
            self.locked_pose = Pose(True, pose.rvec, pose.tvec, pose.n_markers, pose.reproj_px, True)


class Flags:
    """Banderas entre hilos. lock_toggle lo pone asyncio (tecla L) y lo consume el hilo de visión."""

    def __init__(self):
        self.debug_on = threading.Event()
        self.remote_connected = threading.Event()
        self.lock_toggle = threading.Event()


def encode_remote(frame_id, t_ms, bgr, pose_msg, k4, hand, net_cfg):
    """Cuadro chico para el remoto: K escalada al tamaño nuevo, así su raycast da el mismo punto."""
    h, w = bgr.shape[:2]
    rw = net_cfg["remote_width"]
    rh = round(h * rw / w)
    small = cv2.resize(bgr, (rw, rh), interpolation=cv2.INTER_AREA)
    _, jpeg = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, net_cfg["remote_quality"]])
    sx, sy = rw / w, rh / h
    k = [k4[0] * sx, k4[1] * sy, k4[2] * sx, k4[3] * sy]
    return encode_frame(frame_id, t_ms, jpeg.tobytes(), pose_msg, k, [rw, rh], scale_hand(hand, sx, sy))


def scale_hand(hand, sx, sy):
    """Copia de hand con px y box escalados al cuadro chico. Las claves que no están
    (los .dj viejos no tienen box) no se agregan."""
    out = dict(hand)
    if out.get("px") is not None:
        out["px"] = [out["px"][0] * sx, out["px"][1] * sy]
    if out.get("box") is not None:
        u0, v0, u1, v1 = out["box"]
        out["box"] = [u0 * sx, v0 * sy, u1 * sx, v1 * sy]
    return out


def vision_loop(cap, estimator, publish, flags, stop, net_cfg, get_hand=lambda: None):
    """Hilo de captura y visión: lee, estima la pose, codifica y llama a
    publish({frame_id, t, bgr, host_msg, remote_msg, pose}) con cada cuadro.
    get_hand() -> último dict del hilo de manos (o None)."""
    K = estimator.K
    k4 = [K[0, 0], K[1, 1], K[0, 2], K[1, 2]]
    t0, frame_id = time.monotonic(), 0
    while not stop.is_set():
        ok, bgr = cap.read()
        if not ok:
            time.sleep(0.01)
            continue
        t = time.monotonic()
        if flags.lock_toggle.is_set():
            flags.lock_toggle.clear()
            estimator.toggle_lock()
        dbg = flags.debug_on.is_set()
        pose = estimator.update(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), t, debug=dbg)
        t_pose = time.monotonic()
        _, jpeg = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, net_cfg["jpeg_quality"]])
        hand = dict(get_hand() or NO_HAND)
        hand_dbg = hand.pop("dbg", None)
        debug = None
        if dbg:
            debug = {"corners": pose.corners, "ids": pose.ids, "hand": hand_dbg,
                     "ms": {"pose": (t_pose - t) * 1000, "jpeg": (time.monotonic() - t_pose) * 1000}}
        h, w = bgr.shape[:2]
        t_ms = round((t - t0) * 1000)
        pose_msg = pose.to_msg()
        host_msg = encode_frame(frame_id, t_ms, jpeg.tobytes(), pose_msg, k4, [w, h], hand, debug)
        remote_msg = encode_remote(frame_id, t_ms, bgr, pose_msg, k4, hand, net_cfg)             if flags.remote_connected.is_set() else None
        publish({"frame_id": frame_id, "t": t, "bgr": bgr, "host_msg": host_msg, "remote_msg": remote_msg,
                 "pose": pose})
        frame_id += 1
