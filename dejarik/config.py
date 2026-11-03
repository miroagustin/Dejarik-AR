import tomllib

import numpy as np

from dejarik.board import ROOT

CONFIG_PATH = ROOT / "config.toml"
CALIB_PATH = ROOT / "calib.npz"


def load_config(path=CONFIG_PATH):
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_calib(size=None, path=CALIB_PATH):
    """(K, dist, size). Si se pide otra resolución, escala K (mismo aspecto)."""
    data = np.load(path)
    K, dist, calib_size = data["K"].copy(), data["dist"], tuple(int(v) for v in data["size"])
    if size and tuple(size) != calib_size:
        sx, sy = size[0] / calib_size[0], size[1] / calib_size[1]
        K[0] *= sx
        K[1] *= sy
        calib_size = tuple(size)
    return K, dist, calib_size
