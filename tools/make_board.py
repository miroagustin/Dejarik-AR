"""Genera los PDF para imprimir a partir de board_spec.json.

    python tools/make_board.py            -> print/board.pdf (A3, escala 1:1)
    python tools/make_board.py --a4       -> print/board_a4.pdf (A4, tablero achicado)
    python tools/make_board.py --checker  -> print/checker.pdf (damero 9x6 para calibrar)

Imprimir SIEMPRE al 100% ("tamaño real"), nunca "ajustar a página". Después medir
la regla impresa y anotar lo que mide en print_scale_measured de board_spec.json.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dejarik.board import ROOT, board_side_m, load_spec, render_board  # noqa: E402

DPI = 300
PPM = DPI / 0.0254  # píxeles por metro
PAGES_MM = {"A3": (297, 420), "A4": (210, 297)}
MARGIN_MM = 8


def mm(v):
    return int(round(v / 1000 * PPM))


def save_pdf(img_bgr, path):
    path.parent.mkdir(exist_ok=True)
    Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).save(path, "PDF", resolution=DPI)
    print(f"-> {path}")


def draw_ruler(page, x0, y0, scale):
    """Regla de 100 mm nominales, con marcas cada 1 mm (más largas cada 10)."""
    black = (0, 0, 0)
    length = mm(100 * scale)
    cv2.line(page, (x0, y0), (x0 + length, y0), black, 3)
    for i in range(101):
        x = x0 + mm(i * scale)
        h = mm(4) if i % 10 == 0 else mm(2) if i % 5 == 0 else mm(1)
        cv2.line(page, (x, y0), (x, y0 - h), black, 2)
    text = "Medir esta regla y anotar los mm en print_scale_measured (board_spec.json)"
    cv2.putText(page, text, (x0, y0 + mm(6)), cv2.FONT_HERSHEY_SIMPLEX, 1.4, black, 3, cv2.LINE_AA)


def make_board(page_name):
    spec = load_spec(scaled=False)
    w_mm, h_mm = PAGES_MM[page_name]
    side_mm = board_side_m(spec) * 1000
    scale = min(1.0, (w_mm - 2 * MARGIN_MM) / side_mm)
    page = np.full((mm(h_mm), mm(w_mm), 3), 255, np.uint8)

    board, _ = render_board(spec, PPM * scale)
    x0 = (page.shape[1] - board.shape[1]) // 2
    y0 = mm(MARGIN_MM)
    page[y0:y0 + board.shape[0], x0:x0 + board.shape[1]] = board

    draw_ruler(page, mm(MARGIN_MM + 5), y0 + board.shape[0] + mm(20), scale)
    save_pdf(page, ROOT / "print" / ("board.pdf" if page_name == "A3" else "board_a4.pdf"))
    print(f"Escala nominal {scale:.3f}: la regla debería medir {100 * scale:.1f} mm.")


def make_checker(cols=10, rows=7, square_mm=25):
    """10x7 cuadrados = 9x6 esquinas internas, en A4 apaisado."""
    page = np.full((mm(210), mm(297), 3), 255, np.uint8)
    x0 = (page.shape[1] - mm(cols * square_mm)) // 2
    y0 = (page.shape[0] - mm(rows * square_mm)) // 2
    for r in range(rows):
        for c in range(cols):
            if (r + c) % 2 == 0:
                cv2.rectangle(page, (x0 + mm(c * square_mm), y0 + mm(r * square_mm)),
                              (x0 + mm((c + 1) * square_mm) - 1, y0 + mm((r + 1) * square_mm) - 1), (0, 0, 0), -1)
    save_pdf(page, ROOT / "print" / "checker.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a4", action="store_true", help="tablero achicado en una hoja A4")
    ap.add_argument("--checker", action="store_true", help="damero para tools/calibrate.py")
    args = ap.parse_args()
    if args.checker:
        make_checker()
    else:
        make_board("A4" if args.a4 else "A3")
