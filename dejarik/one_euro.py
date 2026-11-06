"""Filtro One-Euro (Casiez et al., 2012) para la pose.

Suaviza mucho cuando la señal está quieta y poco cuando se mueve rápido:
el corte sube con la velocidad (min_cutoff + beta * |dx/dt|).
"""
import math

import numpy as np


def _alpha(cutoff, dt):
    tau = 1.0 / (2 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


class OneEuro:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self.x = self.dx = self.t = None

    def __call__(self, x, t):
        """x: np.ndarray, t: segundos. -> x filtrado."""
        x = np.asarray(x, dtype=np.float64)
        if self.x is None or t <= self.t:
            self.x, self.dx, self.t = x, np.zeros_like(x), t
            return x
        dt = t - self.t
        self.dx = self.dx + _alpha(self.d_cutoff, dt) * ((x - self.x) / dt - self.dx)
        cutoff = self.min_cutoff + self.beta * float(np.linalg.norm(self.dx))
        self.x = self.x + _alpha(cutoff, dt) * (x - self.x)
        self.t = t
        return self.x

    def reset(self):
        self.x = None


def rvec_to_quat(rvec):
    """rvec (eje * ángulo) -> cuaternión [w, x, y, z]."""
    v = np.asarray(rvec, dtype=np.float64).reshape(3)
    angle = float(np.linalg.norm(v))
    if angle < 1e-12:
        return np.array([1.0, 0, 0, 0])
    return np.concatenate([[math.cos(angle / 2)], v / angle * math.sin(angle / 2)])


def quat_to_rvec(q):
    q = np.asarray(q, dtype=np.float64) / np.linalg.norm(q)
    s = float(np.linalg.norm(q[1:]))
    if s < 1e-12:
        return np.zeros(3)
    return q[1:] / s * 2 * math.atan2(s, q[0])


class PoseFilter:
    """Traslación con un One-Euro de 3 componentes; rotación como cuaternión
    (corrige el signo contra el anterior, filtra 4 componentes y renormaliza)."""

    def __init__(self, cfg_t, cfg_r):
        self.ft, self.fr = OneEuro(**cfg_t), OneEuro(**cfg_r)
        self.q_prev = None

    def __call__(self, rvec, tvec, t):
        q = rvec_to_quat(rvec)
        if self.q_prev is not None and np.dot(q, self.q_prev) < 0:
            q = -q
        q = self.fr(q, t)
        q = q / np.linalg.norm(q)
        self.q_prev = q
        return quat_to_rvec(q), self.ft(np.asarray(tvec, dtype=np.float64).reshape(3), t)

    def reset(self):
        self.ft.reset()
        self.fr.reset()
        self.q_prev = None
