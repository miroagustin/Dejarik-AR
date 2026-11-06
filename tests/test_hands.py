import json
import math

import cv2
import numpy as np
import pytest

from dejarik.board import cell_at, cell_center, load_spec
from dejarik.config import load_config
from dejarik.hands import Confirm, gesture_metric, gesture_params, hand_msg, image_to_board
from test_vision import DIST, K, true_pose

SPEC = load_spec()
CLOSED, OPEN = 0.2, 0.6          # con on = 0.35, off = 0.45


def touch(hold_ms=1000, cell_frames=1):
    return Confirm(0.35, 0.45, hold_ms, 0.02, cell_frames, False)


def at(cell, dx=0.0):
    x, y = cell_center(cell, SPEC)
    return (x + dx, y)


def test_image_to_board_roundtrip():
    rvec, tvec = true_pose()
    for cell in (0, 5, 18):
        x, y = cell_center(cell, SPEC)
        uv, _ = cv2.projectPoints(np.array([[x, y, 0.0]]), rvec, tvec, K, DIST)
        bx, by = image_to_board(*uv.ravel(), K, DIST, rvec, tvec)
        assert abs(bx - x) < 1e-6 and abs(by - y) < 1e-6


def test_confirm_fires_once_at_hold_ms():
    c = touch()
    taps = []
    for i in range(16):
        t = i / 10
        taps.append(c.update(CLOSED, 5, at(5), t))
        if i == 0:
            assert c.active and c.hold == 0
        if i == 5:
            assert abs(c.hold - 0.5) < 1e-9
    assert [x for x in taps if x is not None] == [5] and taps[10] == 5
    assert c.hold == 1
    c.update(OPEN, 5, at(5), 1.7)
    assert c.hold == 0


def test_confirm_uses_locked_cell():
    c = touch()
    c.update(CLOSED, 5, at(5), 0.0)
    for t in (0.5, 0.8):
        assert c.update(CLOSED, 6, at(5, 0.010), t) is None
        assert c.shown == 5
    assert c.update(CLOSED, 6, at(5, 0.010), 1.0) == 5
    assert c.shown == 5


def test_confirm_cancels_outside_radius():
    c = touch()
    c.update(CLOSED, 5, at(5), 0.0)
    c.update(CLOSED, 5, at(5, 0.030), 0.5)
    assert c.reason == "salió" and c.hold == 0 and not c.active
    for t in (0.6, 0.7, 2.0):               # sigue cerrado: no vuelve a fijar
        assert c.update(CLOSED, 5, at(5), t) is None and not c.active
    c.update(OPEN, 5, at(5), 2.1)
    c.update(CLOSED, 5, at(5), 2.2)
    assert c.active and c.lock_cell == 5


def test_confirm_edge_lock():
    xy = (0.030, 0.0)                       # casilla 0 tiene ~35 mm de radio
    assert cell_at(*xy, SPEC) == 0
    c = touch()
    taps = [c.update(CLOSED, 0, xy, i / 10) for i in range(12)]
    assert taps[10] == 0 and c.reason == ""


def test_confirm_release_reason():
    c = touch()
    c.update(CLOSED, 5, at(5), 0.0)
    c.update(OPEN, 5, at(5), 0.5)
    assert c.reason == "suelta" and not c.active
    c.update(CLOSED, 5, at(5), 1.0)
    assert c.update(CLOSED, 5, at(5), 2.0) == 5
    c.update(OPEN, 5, at(5), 2.1)
    assert c.reason == "" and not c.active


def test_confirm_cancels_on_lost_hand():
    c = touch()
    c.update(CLOSED, 5, at(5), 0.0)
    c.update(None, None, None, 0.5)
    assert c.reason == "sin mano" and not c.active
    c.update(CLOSED, 5, at(5), 0.6)         # vuelve ya cerrada: fija sin abrir
    assert c.active


def test_confirm_pose_lost():
    c = touch()
    c.update(CLOSED, 5, at(5), 0.0)
    assert c.update(CLOSED, None, None, 0.5) is None
    assert c.reason == "salió" and not c.active


def test_confirm_ignores_start_off_board():
    for cell, xy in ((None, (0.5, 0.5)), (5, None)):
        c = touch()
        c.update(CLOSED, cell, xy, 0.0)
        assert c.reason == "afuera" and not c.active
        c.update(CLOSED, 5, at(5), 0.1)     # hay que abrir para volver a intentar
        assert not c.active
        c.update(OPEN, 5, at(5), 0.2)
        c.update(CLOSED, 5, at(5), 0.3)
        assert c.active


def test_confirm_dwell_two_taps():
    c = Confirm(0.5, 0.5, 1000, 0.02, 3, True)
    assert cell_at(*at(6), SPEC) == 6 and math.dist(at(5), at(6)) > 0.02
    taps, t = [], 0.0
    for _ in range(30):
        taps.append(c.update(0.0, 5, at(5), t))
        t += 0.05
    for _ in range(30):
        taps.append(c.update(0.0, 6, at(6), t))
        t += 0.05
    assert [x for x in taps if x is not None] == [5, 6]
    c = Confirm(0.5, 0.5, 1000, 0.02, 3, True)
    c.update(0.0, None, (0.5, 0.5), 0.0)
    assert c.reason == "afuera" and c.armed


def test_confirm_hold_ms_zero():
    c = touch(hold_ms=0)
    assert c.update(CLOSED, 5, at(5), 0.0) is None and c.active and c.hold == 1
    assert c.update(CLOSED, 5, at(5), 0.03) == 5


def test_confirm_debounce():
    c = touch(cell_frames=3)
    for i, cell in enumerate([5, 5, 5]):
        c.update(OPEN, cell, at(5), i)
    assert c.shown == 5
    c.update(OPEN, 6, at(6), 3)
    c.update(OPEN, 5, at(5), 4)
    assert c.shown == 5
    c.update(OPEN, 6, at(6), 5)
    c.update(OPEN, 6, at(6), 6)
    assert c.shown == 5
    c.update(OPEN, 6, at(6), 7)
    assert c.shown == 6
    c.update(CLOSED, 7, at(7), 8)           # cerrado sobre una casilla que todavía no es shown
    c.update(CLOSED, 7, at(7), 9)
    assert not c.active
    c.update(CLOSED, 7, at(7), 10)
    assert c.active and c.lock_cell == 7


def hand_lmw(bent=False):
    w = np.zeros((21, 3))
    w[9] = (0, 0.09, 0)
    w[10] = (0.01, 0.10, 0)
    w[12] = (0.01, 0.09, 0.02) if bent else (0.01, 0.17, 0)
    w[8] = (-0.005, 0.17, 0)
    return w


def test_gesture_metric():
    lm2d = np.zeros((21, 2))
    assert gesture_metric("touch", lm2d, hand_lmw(), 1.15) < 0.35
    assert gesture_metric("touch", lm2d, hand_lmw(bent=True), 1.05) == math.inf
    assert gesture_metric("dwell", lm2d, hand_lmw(), 1.15) == 0.0
    with pytest.raises(ValueError):
        gesture_metric("pinch", lm2d, hand_lmw(), 1.15)


def test_gesture_params():
    cfg = dict(load_config()["hands"])
    p = gesture_params(cfg)
    assert p["gesture"] == "touch" and not p["rearm_on_move"]
    assert abs(p["cancel_radius_m"] - cfg["cancel_radius_mm"] / 1000) < 1e-12
    p = gesture_params(dict(cfg, gesture="dwell"))
    assert p["rearm_on_move"] and p["on"] == p["off"] == 0.5
    with pytest.raises(ValueError):
        gesture_params(dict(cfg, gesture="pinch"))


def test_hand_msg():
    c = touch()
    lm2d = np.array([[100.0 + i * 5, 50.0 + i * 5] for i in range(21)])
    m = hand_msg(c, lm2d, math.inf, np.float64(0.4), np.bool_(True), 0.15)
    assert m["box"] == [85.0, 35.0, 215.0, 165.0] and m["px"] == [140.0, 90.0]
    assert m["dbg"]["metric"] is None and m["dbg"]["extended"] is True
    assert hand_msg(c, lm2d, 0.0, 0.4, False, 0.15)["dbg"]["metric"] == 0.0
    json.dumps(m)
    json.dumps(hand_msg(c, None, None, None, False, 0.15))
