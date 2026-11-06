import numpy as np

from dejarik.config import load_config
from dejarik.one_euro import OneEuro, PoseFilter, quat_to_rvec, rvec_to_quat

CFG = load_config()["filter"]


def test_reduces_noise():
    rng = np.random.default_rng(0)
    f = OneEuro(**CFG["t"])
    x = 0.6 + rng.normal(0, 0.001, 300)
    y = np.array([f(np.array([v]), i / 30)[0] for i, v in enumerate(x)])
    assert y[30:].std() < x[30:].std() / 2


def test_follows_step():
    f = OneEuro(**CFG["t"])
    for i in range(30):
        f(np.array([0.0]), i / 30)
    out = [f(np.array([1.0]), (30 + i) / 30)[0] for i in range(10)]
    assert out[-1] > 0.9


def test_quat_roundtrip():
    r = np.array([0.3, -1.2, 2.0])
    assert np.allclose(quat_to_rvec(rvec_to_quat(r)), r)


def test_quat_sign_flip_no_jump():
    f = PoseFilter(CFG["t"], CFG["r"])
    r = np.array([0.0, 0.0, 3.1])
    out = []
    for i in range(20):
        q = rvec_to_quat(r)
        rv = quat_to_rvec(-q if i % 2 else q)  # mismo giro, cuaternión con el signo cambiado
        out.append(f(rv, np.zeros(3), i / 30)[0])
    rot = [rvec_to_quat(o) for o in out]
    assert all(abs(abs(np.dot(rot[0], q)) - 1) < 1e-6 for q in rot)
