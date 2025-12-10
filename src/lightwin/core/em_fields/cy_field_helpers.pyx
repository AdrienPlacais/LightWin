#cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
from libc.math cimport cos, sin


cdef class RealEzFuncCython:
    """Fast Cython implementation of E(z)*cos(phi) for RK4."""
    cdef double[:] positions
    cdef double[:] field_values
    cdef double amplitude
    cdef double phi0_rel

    def __init__(self, positions, field_values, double amplitude, double phi0_rel):
        self.positions = positions
        self.field_values = field_values
        self.amplitude = amplitude
        self.phi0_rel = phi0_rel

    def __call__(self, double z, double phi):
        cdef double[:] positions = self.positions
        cdef double[:] field_values = self.field_values

        # quick boundary check
        if z < positions[0] or z > positions[positions.shape[0]-1]:
            return 0.0

        # find index
        cdef double frac = (z - positions[0]) / (positions[positions.shape[0]-1] - positions[0])
        cdef Py_ssize_t i = <Py_ssize_t>(frac * (positions.shape[0] - 1))

        if i < 0:
            i = 0
        elif i >= positions.shape[0] - 1:
            i = positions.shape[0] - 2

        # linear interpolation
        cdef double pos0 = positions[i]
        cdef double t = (z - pos0) / (positions[i+1] - pos0)

        cdef double e = field_values[i] * (1 - t) + field_values[i+1] * t

        # RF phase
        return self.amplitude * e * cos(phi + self.phi0_rel)


cdef class ComplexEzFuncCython:
    """Same as RealEzFuncCython but returning a complex value."""
    cdef double[:] positions
    cdef double[:] field_values
    cdef double amplitude
    cdef double phi0_rel

    def __init__(self, positions, field_values, double amplitude, double phi0_rel):
        self.positions = positions
        self.field_values = field_values
        self.amplitude = amplitude
        self.phi0_rel = phi0_rel

    def __call__(self, double z, double phi):
        cdef double[:] positions = self.positions
        cdef double[:] field_values = self.field_values

        if z < positions[0] or z > positions[positions.shape[0]-1]:
            return 0.0

        cdef double frac = (z - positions[0]) / (positions[positions.shape[0]-1] - positions[0])
        cdef Py_ssize_t i = <Py_ssize_t>(frac * (positions.shape[0] - 1))

        if i < 0:
            i = 0
        elif i >= positions.shape[0] - 1:
            i = positions.shape[0] - 2

        cdef double pos0 = positions[i]
        cdef double t = (z - pos0) / (positions[i+1] - pos0)
        cdef double e = field_values[i] * (1 - t) + field_values[i+1] * t

        cdef double total_phase = phi + self.phi0_rel

        return self.amplitude * e * (cos(total_phase) + 1j*sin(total_phase))
