import math

import cv2
import numpy as np

from dejarik.board import load_spec, marker_corners
from dejarik.config import load_config
from dejarik.vision import PoseEstimator, _rot_angle_deg, to_view_matrix

K = np.array([[900.0, 0, 640], [0, 900.0, 360], [0, 0, 1]])
DIST = np.zeros(5)


def true_pose(distance=0.6, tilt_deg=40.0):
    """Cámara arriba del tablero, inclinada tilt_deg, a `distance` del centro."""
    tilt, _ = cv2.Rodrigues(np.array([math.radians(tilt_deg), 0, 0]))
    R = tilt @ np.diag([1.0, -1.0, -1.0])
    rvec, _ = cv2.Rodrigues(R)
    return rvec.ravel(), np.array([0.0, 0.0, distance])


def projected(spec, rvec, tvec, ids, noise_px=0.3, seed=0):
    rng = np.random.default_rng(seed)
    mc = marker_corners(spec)
    corners = []
    for i in ids:
        px, _ = cv2.projectPoints(mc[i].astype(np.float64), rvec, tvec, K, DIST)
        corners.append((px.reshape(1, 4, 2) + rng.normal(0, noise_px, (1, 4, 2))).astype(np.float32))
    return tuple(corners), np.array(ids, dtype=np.int32).reshape(-1, 1)


def estimator():
    return PoseEstimator(load_spec(), K, DIST, load_config())


def check_recovers(ids):
    spec = load_spec()
    rvec, tvec = true_pose()
    est_r, est_t, err = estimator().solve(*projected(spec, rvec, tvec, ids))
    assert np.linalg.norm(est_t - tvec) * 1000 < 2.0
    assert _rot_angle_deg(rvec, est_r) < 1.0
    assert err < 1.0


def test_recovers_pose_all_markers():
    check_recovers(list(range(12)))


def test_recovers_pose_two_markers():
    check_recovers([0, 3])


def test_view_matrix_identity():
    T = np.array(to_view_matrix(np.zeros(3), np.zeros(3))).reshape(4, 4, order="F")
    assert np.allclose(T, np.diag([1, -1, -1, 1]))


def test_rejects_high_reprojection():
    spec = load_spec()
    rvec, tvec = true_pose()
    corners, ids = projected(spec, rvec, tvec, list(range(12)), noise_px=0)
    corners = tuple(c + np.float32(np.random.default_rng(1).normal(0, 8, c.shape)) for c in corners)
    est = estimator()
    _, _, err = est.solve(corners, ids)
    assert err > est.p["max_reproj_px"]


def test_update_on_rendered_frame_holds_then_loses():
    """De punta a punta sobre una imagen: detecta, mantiene 0,5 s sin marcadores y después pierde."""
    from tools.fake_session import render_frame
    from dejarik.board import render_board
    spec = load_spec()
    board_img, A = render_board(spec, ppm=4000)
    rvec, tvec = true_pose()
    gray = cv2.cvtColor(render_frame(board_img, A, rvec, tvec), cv2.COLOR_BGR2GRAY)
    est = estimator()
    pose = est.update(gray, t=0.0)
    assert pose.ok and pose.n_markers == 12
    assert np.linalg.norm(pose.tvec - tvec) * 1000 < 2.0
    blank = np.full_like(gray, 128)
    assert est.update(blank, t=0.3).ok
    assert not est.update(blank, t=0.7).ok


def test_vision_loop_publishes_host_and_remote():
    import threading
    from dejarik.board import render_board
    from dejarik.protocol import decode_frame
    from dejarik.vision import Flags, vision_loop
    from tools.fake_session import render_frame
    spec = load_spec()
    board_img, A = render_board(spec, ppm=4000)
    bgr = render_frame(board_img, A, *true_pose())
    stop, flags, got = threading.Event(), Flags(), []
    flags.remote_connected.set()
    flags.debug_on.set()

    class Cap:
        def read(self):
            return True, bgr

    def publish(pkt):
        got.append(pkt)
        if len(got) == 3:
            stop.set()
    vision_loop(Cap(), estimator(), publish, flags, stop, load_config()["net"])
    h, _ = decode_frame(got[-1]["host_msg"])
    r, _ = decode_frame(got[-1]["remote_msg"])
    assert h["pose"]["ok"] and h["size"] == [1280, 720] and len(h["debug"]["ids"]) == 12
    assert r["size"] == [854, 480] and abs(r["K"][0] - 900 * 854 / 1280) < 1e-6 and "debug" not in r


def test_encode_remote_scales_hand():
    from dejarik.protocol import decode_frame
    from dejarik.vision import encode_remote
    bgr = np.zeros((720, 1280, 3), np.uint8)
    net_cfg = {"remote_width": 640, "remote_quality": 60}
    hand = {"cell": 3, "pinch": False, "px": [100, 50], "hold": 0.5, "box": [10, 20, 30, 40]}
    h, _ = decode_frame(encode_remote(0, 0, bgr, {"ok": False}, [1000, 1000, 640, 360], hand, net_cfg))
    assert h["hand"]["px"] == [50, 25] and h["hand"]["box"] == [5, 10, 15, 20]
    assert hand["px"] == [100, 50] and hand["box"] == [10, 20, 30, 40]
    old = {"cell": None, "pinch": False, "px": [100, 50]}          # .dj viejo: sin box
    h, _ = decode_frame(encode_remote(0, 0, bgr, {"ok": False}, [1000, 1000, 640, 360], old, net_cfg))
    assert h["hand"]["px"] == [50, 25] and "box" not in h["hand"]
