General structure of the code
-----------------------------

The highest-level object is an :class:`.Accelerator`.
It is initialized thanks to a ``.dat`` file (the same format as TraceWin).
Its main purpose is to store a :class:`.ListOfElements`, which is a ``list`` containing all the :class:`.Element`\s of the ``.dat`` file.

The propagation of the beam through the accelerator is performed thanks to a :class:`.BeamCalculator`.
As for now, three different :class:`.BeamCalculator`\s are implemented:
* :class:`.Envelope1D`, which computes the propagation of the beam in envelope and in 1D (longitudinal).
* :class:`.Envelope3D`, which computes the propagation of the beam in envelope and in 3D.
* :class:`.TraceWin`, which simply calls TraceWin from the command-line interface.

All :class:`.BeamCalculator`\s have a :meth:`.BeamCalculator.run` method, which perform the beam dynamics calculation along the linac; it takes in a :class:`.ListOfElements` and returns a :class:`.SimulationOutput`.
This last object contains all the useful information, such as kinetic energy along the linac.

