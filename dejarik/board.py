"""Geometría del tablero. Todo sale de board_spec.json.

Sistema del tablero: origen en el centro, metros, Z hacia arriba saliendo del
papel, X hacia el centro del sector 1, sectores antihorarios vistos desde arriba.
"""
import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "board_spec.json"


def load_spec(path=SPEC_PATH, scaled=True):
    """Lee el spec. Con scaled=True corrige todas las longitudes por lo que
    midió de verdad la regla de 100 mm impresa (print_scale_measured)."""
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    if scaled:
        s = spec["print_scale_measured"] / 100.0
        spec["radii_m"] = {k: v * s for k, v in spec["radii_m"].items()}
        for m in spec["markers"]:
            m["center_xy_m"] = [c * s for c in m["center_xy_m"]]
            m["size_m"] *= s
    return spec


def marker_corners(spec):
    """{id: float32 (4,3)} en el orden de ArUco: arriba-izq, arriba-der,
    abajo-der, abajo-izq (horario visto desde arriba), z = 0.
    rotation_deg es la dirección "arriba" del marcador, antihoraria desde +X."""
    out = {}
    for m in spec["markers"]:
        cx, cy = m["center_xy_m"]
        h = m["size_m"] / 2
        a = math.radians(m["rotation_deg"])
        up = np.array([math.cos(a), math.sin(a)])
        right = np.array([math.sin(a), -math.cos(a)])
        c = np.array([cx, cy])
        pts = [c + h * (-right + up), c + h * (right + up), c + h * (right - up), c + h * (-right - up)]
        out[m["id"]] = np.array([[p[0], p[1], 0.0] for p in pts], dtype=np.float32)
    return out


def dictionary(spec):
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, spec["dictionary"]))


def aruco_board(spec):
    corners = marker_corners(spec)
    ids = sorted(corners)
    return cv2.aruco.Board([corners[i] for i in ids], dictionary(spec), np.array(ids, dtype=np.int32))


def cell_at(x, y, spec):
    """Punto del plano del tablero -> número de casilla, o None si cae afuera."""
    r = math.hypot(x, y)
    radii = spec["radii_m"]
    if r < radii["r0"]:
        return 0
    if r > radii["r2"]:
        return None
    ang = (math.degrees(math.atan2(y, x)) - spec["sector_offset_deg"] + 15) % 360
    sector = int(ang // 30) % 12 + 1
    return sector if r < radii["r1"] else 12 + sector


def cell_center(cell, spec):
    if cell == 0:
        return (0.0, 0.0)
    radii = spec["radii_m"]
    r = (radii["r0"] + radii["r1"]) / 2 if cell <= 12 else (radii["r1"] + radii["r2"]) / 2
    sector = (cell - 1) % 12 + 1
    a = math.radians(spec["sector_offset_deg"] + (sector - 1) * 30)
    return (r * math.cos(a), r * math.sin(a))


def neighbors(cell, spec):
    return spec["adjacency"][str(cell)]


def board_side_m(spec, margin=0.004):
    """Lado del cuadrado que contiene anillos y marcadores, con un margen blanco."""
    far = max(float(np.hypot(p[0], p[1])) for c in marker_corners(spec).values() for p in c)
    return 2 * (max(far, spec["radii_m"]["r2"]) + margin)


def render_board(spec, ppm, size_m=None):
    """Dibuja el tablero (blanco y negro, listo para imprimir).
    ppm = píxeles por metro. Devuelve (imagen BGR, A) donde A (3x3) lleva
    píxel (u, v, 1) -> punto del tablero (x, y, 1). u a la derecha, v hacia abajo."""
    side = size_m or board_side_m(spec)
    n = int(round(side * ppm))
    img = np.full((n, n, 3), 255, np.uint8)
    c = n / 2

    def px(x, y):
        return (int(round(c + x * ppm)), int(round(c - y * ppm)))

    radii = spec["radii_m"]
    thick = max(1, int(0.0008 * ppm))
    for r in radii.values():
        cv2.circle(img, px(0, 0), int(round(r * ppm)), (0, 0, 0), thick, cv2.LINE_AA)
    for k in range(12):
        a = math.radians(spec["sector_offset_deg"] + k * 30 + 15)
        cv2.line(img, px(radii["r0"] * math.cos(a), radii["r0"] * math.sin(a)),
                 px(radii["r2"] * math.cos(a), radii["r2"] * math.sin(a)), (0, 0, 0), thick, cv2.LINE_AA)
    arm = 0.006
    cv2.line(img, px(-arm, 0), px(arm, 0), (0, 0, 0), thick, cv2.LINE_AA)
    cv2.line(img, px(0, -arm), px(0, arm), (0, 0, 0), thick, cv2.LINE_AA)

    font_scale = 0.00012 * ppm
    for cell in range(1, 25):
        x, y = cell_center(cell, spec)
        label = str(cell)
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thick)
        u, v = px(x, y)
        cv2.putText(img, label, (u - w // 2, v + h // 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                    (150, 150, 150), thick, cv2.LINE_AA)

    d = dictionary(spec)
    corners_by_id = marker_corners(spec)
    for m in spec["markers"]:
        size_px = 6 * 60  # 6 celdas (4x4 + borde), 60 px por celda; se reescala al pegarlo
        tag = cv2.aruco.generateImageMarker(d, m["id"], size_px)
        src = np.float32([[0, 0], [size_px, 0], [size_px, size_px], [0, size_px]])
        dst = np.float32([[c + p[0] * ppm, c - p[1] * ppm] for p in corners_by_id[m["id"]]])
        M = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(tag, M, (n, n), flags=cv2.INTER_NEAREST, borderValue=255)
        mask = cv2.warpPerspective(np.full_like(tag, 255), M, (n, n), flags=cv2.INTER_NEAREST)
        img[mask > 0] = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)[mask > 0]

    A = np.array([[1 / ppm, 0, -c / ppm], [0, -1 / ppm, c / ppm], [0, 0, 1]])
    return img, A
