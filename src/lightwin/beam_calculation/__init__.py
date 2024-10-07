"""Compute propagation of beam in the linac.

:class:`.BeamCalculator` is an Abstract Base Class to hold such a solver.
:class:`.Envelope1D`, :class:`.Envelope3D` and :class:`.TraceWin` are the
implemented solvers inheriting from it. They can be created very easily using
the :mod:`.beam_calculation.factory` module.

:class:`.SimulationOutput` is used to uniformly store simulation outputs with
all solvers.

In order to work, solvers rely on :class:`.ElementBeamCalculatorParameters` to
hold the meshing, etc.

"""
