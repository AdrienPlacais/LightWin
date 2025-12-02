"""Define Runge-Kutta integration functions (Cython).

Currently unused, RK4 integration is directly typed where necessary.

"""

from libc.math cimport cos, sin, sqrt

import numpy as np

cimport numpy as np

ctypedef np.float64_t DTYPE_t

def rk4(np.ndarray[DTYPE_t, ndim=1] u,
        du,
        double x,
        double dx):
    cdef double half_dx = 0.5 * dx
    cdef np.ndarray[DTYPE_t, ndim=1] k1, k2, k3, k4
    k1 = du(x, u)
    k2 = du(x + half_dx, u + 0.5 * k1)
    k3 = du(x + half_dx, u + 0.5 * k2)
    k4 = du(x + dx, u + k3)
    return (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0

def rk4_2d(double u,
           double v,
           delta,
           double x,
           double dx):
    cdef double half_dx = 0.5 * dx
    cdef double k1u, k1v, k2u, k2v, k3u, k3v, k4u, k4v
    k1u, k1v = delta(x, u, v)
    k2u, k2v = delta(x + half_dx, u + 0.5 * k1u, v + 0.5 * k1v)
    k3u, k3v = delta(x + half_dx, u + 0.5 * k2u, v + 0.5 * k2v)
    k4u, k4v = delta(x + dx, u + k3u, v + k3v)
    return ((k1u + 2*k2u + 2*k3u + k4u)/6.0,
            (k1v + 2*k2v + 2*k3v + k4v)/6.0)

