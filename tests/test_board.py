import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from dejarik.board import (aruco_board, cell_at, cell_center, dictionary, load_spec, marker_corners,
                           neighbors, render_board)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from fake_session import K, render_frame, synthetic_pose  # noqa: E402

SPEC = load_spec()


def test_adjacency_is_symmetric():
    for a, ns in SPEC["adjacency"].items():
        for b in ns:
            assert int(a) in neighbors(b, SPEC)


def test_neighbor_counts():
    assert len(neighbors(0, SPEC)) == 12
    assert all(len(neighbors(c, SPEC)) == 4 for c in range(1, 13))
    assert all(len(neighbors(c, SPEC)) == 3 for c in range(13, 25))


def test_cell_center_roundtrip():
    for c in range(25):
        assert cell_at(*cell_center(c, SPEC), SPEC) == c


def test_outside_board_is_none():
    assert cell_at(SPEC["radii_m"]["r2"] + 0.001, 0, SPEC) is None


def test_sector_1_is_on_plus_x_and_sectors_go_counterclockwise():
    r = (SPEC["radii_m"]["r0"] + SPEC["radii_m"]["r1"]) / 2
    assert cell_at(r, 0, SPEC) == 1
    assert cell_at(r * math.cos(math.radians(30)), r * math.sin(math.radians(30)), SPEC) == 2
    assert cell_at(0, -r, SPEC) == 10


def test_marker_corners_flat_and_sized():
    for mid, c in marker_corners(SPEC).items():
        assert np.allclose(c[:, 2], 0)
        size = next(m["size_m"] for m in SPEC["markers"] if m["id"] == mid)
        assert np.linalg.norm(c[1] - c[0]) == pytest.approx(size, rel=1e-5)


def test_print_scale_corrects_lengths(tmp_path):
    raw = load_spec(scaled=False)
    raw["print_scale_measured"] = 98.0  # la regla impresa midió 98 mm
    (tmp_path / "spec.json").write_text(json.dumps(raw), encoding="utf-8")
    small = load_spec(tmp_path / "spec.json")
    nominal = load_spec(scaled=False)
    assert small["radii_m"]["r2"] == pytest.approx(nominal["radii_m"]["r2"] * 0.98)
    assert small["markers"][0]["size_m"] == pytest.approx(nominal["markers"][0]["size_m"] * 0.98)


@pytest.mark.parametrize("phase", [0.0, 0.25, 0.6])
def test_rendered_board_gives_back_its_pose(phase):
    """Contrato del día 2: el tablero dibujado, el spec y el orden de esquinas
    coinciden. Si alguno está mal, la pose recuperada no da la verdadera."""
    board_img, A = render_board(SPEC, ppm=4000)
    rvec, tvec = synthetic_pose(phase)
    gray = cv2.cvtColor(render_frame(board_img, A, rvec, tvec), cv2.COLOR_BGR2GRAY)

    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    corners, ids, _ = cv2.aruco.ArucoDetector(dictionary(SPEC), params).detectMarkers(gray)
    assert ids is not None and len(ids) == 12

    obj, img = aruco_board(SPEC).matchImagePoints(corners, ids)
    ok, r_est, t_est = cv2.solvePnP(obj, img, K, None, flags=cv2.SOLVEPNP_IPPE)
    assert ok
    assert np.linalg.norm(t_est.ravel() - tvec) < 0.002  # < 2 mm
    R_err = cv2.Rodrigues(r_est)[0].T @ cv2.Rodrigues(rvec)[0]
    assert np.degrees(np.linalg.norm(cv2.Rodrigues(R_err)[0])) < 1.0
