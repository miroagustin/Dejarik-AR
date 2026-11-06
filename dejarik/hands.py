"""Mano: MediaPipe HandLandmarker -> casilla bajo el índice y gesto de confirmación
(ver docs/designs/hand_interaction.md).

"Apoyá el índice en una casilla y sostené": la punta del índice apoyada en el papel
elige la casilla, y quedarse quieto hold_ms (gesture = "dwell", el de por defecto)
equivale a un clic sobre esa casilla. Con gesture = "touch" además hay que juntar el
medio con el índice.
"""
import math
import time

import cv2
import numpy as np

from dejarik.board import ROOT, cell_at

MODEL_PATH = ROOT / "models" / "hand_landmarker.task"
NO_HAND = {"cell": None, "pinch": False, "px": None, "hold": 0, "box": None}
GESTURES = ("touch", "dwell")


def _d(a, b):
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))


def middle_ratio(lmw):
    """Largo del medio relativo al índice: |w12-w0| / |w8-w0|. Estirado ~1, doblado ~0,5.
    Relativo al índice (que apunta) y no a la propia falange: visto desde el lado de
    enfrente los dos dedos se acortan igual y el ratio no cambia."""
    return _d(lmw[12], lmw[0]) / max(1e-6, _d(lmw[8], lmw[0]))


def middle_extended(lmw, thresh):
    """bool de Python (json.dumps)."""
    return bool(middle_ratio(lmw) > thresh)


def gesture_metric(gesture, lm2d, lmw, ext_thresh):
    """Métrica que va a Confirm: chica = "cerrado". inf = abierto (medio doblado)."""
    if gesture == "touch":
        if not middle_extended(lmw, ext_thresh):
            return math.inf
        return _d(lmw[8], lmw[12]) / max(1e-6, _d(lmw[0], lmw[9]))
    if gesture == "dwell":
        return 0.0
    raise ValueError(f"gesture desconocido: {gesture!r}")


def metric_2d(lm2d):
    """El mismo ratio en píxeles, solo para el debug (comparar 2D contra 3D en E1)."""
    return _d(lm2d[8], lm2d[12]) / max(1e-6, _d(lm2d[0], lm2d[9]))


def gesture_params(cfg):
    """cfg es la tabla [hands]. Valida gesture al arrancar el hilo."""
    gesture = cfg["gesture"]
    if gesture not in GESTURES:
        raise ValueError(f"[hands] gesture = {gesture!r}; tiene que ser uno de {GESTURES}")
    dwell = gesture == "dwell"
    return {
        "gesture": gesture,
        "on": 0.5 if dwell else cfg["on"],
        "off": 0.5 if dwell else cfg["off"],
        "ext_on": 0.0 if dwell else cfg["extended_on"],
        "ext_off": 0.0 if dwell else cfg["extended_off"],
        "hold_ms": cfg["hold_ms"],
        "cancel_radius_m": cfg["cancel_radius_mm"] / 1000,
        "cell_frames": cfg["cell_frames"],
        "box_margin": cfg["box_margin"],
        "rearm_on_move": dwell,
    }


class Confirm:
    """Máquina de estados del gesto: la tabla de la sección 3 del design.
    update() -> casilla confirmada (una sola vez por intento) o None."""

    def __init__(self, on, off, hold_ms, cancel_radius_m, cell_frames, rearm_on_move, cell_ok=lambda c: True):
        self.on, self.off, self.hold_s = on, off, hold_ms / 1000
        self.radius, self.cell_frames, self.rearm_on_move = cancel_radius_m, cell_frames, rearm_on_move
        self.armed, self.lock_cell, self.lock_xy, self.t0, self.fired = True, None, None, None, False
        self.reason, self.shown, self.cand, self.cand_n, self.t_last = "", None, None, 0, 0
        self.bad_n, self.dist = 0, None  # cuadros seguidos abierto/afuera; distancia a lock_xy (m)
        self.cell_ok = cell_ok           # el juego dice si tocar esa casilla ahora tiene sentido

    @property
    def active(self):
        return self.lock_cell is not None

    @property
    def hold(self):
        if not self.active:
            return 0
        if self.fired or self.hold_s == 0:
            return 1
        return min(1, (self.t_last - self.t0) / self.hold_s)

    def _update_shown(self, cell):
        if self.active:
            self.shown = self.lock_cell
        elif cell == self.shown:
            self.cand, self.cand_n = None, 0
        else:
            self.cand_n = self.cand_n + 1 if cell == self.cand else 1
            self.cand = cell
            if self.cand_n >= self.cell_frames:
                self.shown, self.cand, self.cand_n = cell, None, 0

    def _free(self, reason, armed):
        if not self.fired:  # después de disparar, reason queda en "" (lo puso el fijado)
            self.reason = reason
        self.lock_cell, self.lock_xy, self.armed = None, None, armed

    def update(self, metric, cell, xy, t):
        self.t_last = t
        self._update_shown(cell)
        if metric is None:
            if self.active:
                self._free("sin mano", True)
            self.armed = True
            return None
        if self.active:
            self.dist = None if xy is None else math.dist(xy, self.lock_xy)
            opened = metric > self.off
            out = self.dist is None or self.dist > self.radius
            # Abrir o salir del radio tiene que durar cell_frames cuadros seguidos: un cuadro
            # suelto de temblor del landmark (sobre todo desde el lado lejano) no cancela.
            if opened or out:
                self.bad_n += 1
                if self.bad_n >= self.cell_frames:
                    if opened:
                        self._free("suelta", True)
                    else:
                        self._free("salió", self.rearm_on_move)
                return None
            self.bad_n = 0
            if not self.fired and t - self.t0 >= self.hold_s:
                self.fired = True
                return self.lock_cell
            return None
        if not self.armed:
            if metric > self.off:
                self.armed = True
            return None
        if metric >= self.on:
            return None
        if cell is None or xy is None:
            self.reason, self.armed = "afuera", self.rearm_on_move
        elif cell == self.shown and self.cell_ok(cell):
            self.lock_cell, self.lock_xy, self.t0, self.fired, self.reason = cell, tuple(xy), t, False, ""
            self.cand, self.cand_n, self.bad_n, self.dist = None, 0, 0, 0.0
        return None


def hand_msg(conf, lm2d, metric, metric2d, extended, box_margin, ext=None):
    """Dict que se publica en "hand" (+ "dbg" para el overlay). Solo floats/bools de
    Python: encode_frame hace json.dumps."""
    if lm2d is None:
        return dict(NO_HAND, cell=conf.shown, dbg={"metric": None, "metric2d": None, "ext": None, "extended": False,
                                                   "hold": 0, "lock_cell": None, "reason": conf.reason})
    hold = round(float(conf.hold), 2)
    (u0, v0), (u1, v1) = lm2d.min(axis=0), lm2d.max(axis=0)
    mx, my = box_margin * (u1 - u0), box_margin * (v1 - v0)
    box = [round(float(x), 1) for x in (u0 - mx, v0 - my, u1 + mx, v1 + my)]
    return {"cell": conf.shown, "pinch": conf.active,
            "px": [round(float(lm2d[8][0]), 1), round(float(lm2d[8][1]), 1)],
            "hold": hold, "box": box,
            "dbg": {"metric": None if math.isinf(metric) else round(float(metric), 3),
                    "metric2d": round(float(metric2d), 3),
                    "ext": None if ext is None else round(float(ext), 3), "extended": bool(extended),
                    "hold": hold, "lock_cell": conf.lock_cell, "reason": conf.reason,
                    "dist_mm": None if conf.dist is None else round(conf.dist * 1000, 1)}}


def image_to_board(u, v, K, dist, rvec, tvec):
    """Píxel de la imagen -> (x, y) en el plano del tablero, con H = K [r1 r2 t]."""
    pt = cv2.undistortPoints(np.array([[[u, v]]], np.float64), K, dist, P=K).reshape(2)
    R, _ = cv2.Rodrigues(np.asarray(rvec, np.float64).reshape(3, 1))
    H = K @ np.column_stack([R[:, 0], R[:, 1], np.asarray(tvec, np.float64).reshape(3)])
    x, y, w = np.linalg.solve(H, [pt[0], pt[1], 1.0])
    return x / w, y / w


class HandTracker:
    def __init__(self, cfg, model_path=MODEL_PATH):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
        self.mp = mp
        self.landmarker = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO, num_hands=1))
        self.width = cfg["input_width"]
        self.last_ms = -1

    def landmarks(self, bgr, t):
        """-> (lm2d, lmw) o None. lm2d: (21, 2) en píxeles de la imagen completa;
        lmw: (21, 3) world landmarks en metros (escala estimada: solo se usan ratios)."""
        h, w = bgr.shape[:2]
        small = cv2.resize(bgr, (self.width, round(h * self.width / w)), interpolation=cv2.INTER_AREA)
        ms = max(int(t * 1000), self.last_ms + 1)  # MediaPipe exige timestamps estrictamente crecientes
        self.last_ms = ms
        res = self.landmarker.detect_for_video(
            self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB)), ms)
        if not res.hand_landmarks:
            return None
        lm2d = np.array([[p.x * w, p.y * h] for p in res.hand_landmarks[0]])
        lmw = np.array([[p.x, p.y, p.z] for p in res.hand_world_landmarks[0]])
        return lm2d, lmw


def hands_loop(get_packet, publish_hand, on_tap, stop, K, dist, spec, cfg, cell_ok=lambda c: True):
    """Hilo de manos. get_packet() -> último paquete del frame_bus (o None);
    publish_hand(dict) deja el campo "hand" (+ "dbg") para el próximo cuadro;
    on_tap(cell) se llama cuando Confirm confirma un gesto (siempre con la pose ok);
    cell_ok(cell) dice si el anillo puede arrancar sobre esa casilla (ver Server.hand_cell_ok)."""
    p = gesture_params(cfg)
    tracker = HandTracker(cfg)
    conf = Confirm(p["on"], p["off"], p["hold_ms"], p["cancel_radius_m"], p["cell_frames"], p["rearm_on_move"],
                   cell_ok)
    last_id, min_dt, next_t = None, 1 / cfg["max_fps"], 0.0
    while not stop.is_set():
        pkt = get_packet()
        # Tope de cuadros por segundo: con varias manos en cuadro MediaPipe re-detecta
        # palmas seguido y, sin tope, le saca CPU a la pose y al video.
        if pkt is None or pkt["frame_id"] == last_id or time.monotonic() < next_t:
            time.sleep(0.005)
            continue
        last_id, next_t = pkt["frame_id"], time.monotonic() + min_dt
        t = pkt["t"]
        t_mp = time.perf_counter()
        res = tracker.landmarks(pkt["bgr"], t)
        ms = round((time.perf_counter() - t_mp) * 1000, 1)
        if res is None:
            conf.update(None, None, None, t)
            msg = hand_msg(conf, None, None, None, False, p["box_margin"])
            msg["dbg"]["ms"] = ms
            publish_hand(msg)
            continue
        lm2d, lmw = res
        ext_thresh = p["ext_off"] if conf.active else p["ext_on"]
        extended = middle_extended(lmw, ext_thresh)
        metric = gesture_metric(p["gesture"], lm2d, lmw, ext_thresh)
        pose = pkt["pose"]
        xy = cell = None
        if pose.ok:
            xy = image_to_board(*lm2d[8], K, dist, pose.rvec, pose.tvec)
            cell = cell_at(*xy, spec)
        tap = conf.update(metric, cell, xy, t)
        if tap is not None:
            on_tap(tap)
        msg = hand_msg(conf, lm2d, metric, metric_2d(lm2d), extended, p["box_margin"], middle_ratio(lmw))
        msg["dbg"]["ms"] = ms
        publish_hand(msg)
