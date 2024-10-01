Breaking and fixing a linac
---------------------------

The methods to break -- and then fix -- a linac are stored in the :class:`.Fault` objects, gathered in :class:`.FaultScenario`.
A :class:`.Fault` is composed of one or several failed cavities that are fixed together.
A :class:`.FaultScenario` is composed of one or several :class:`.Fault` happening at the same time.

The compensation is realized by an :class:`.OptimisationAlgorithm`.
It will try to find the *best* :class:`.Variable`\s that match the :class:`.Objective`\s while respecting the :class:`.Constraint`\s.
Under the hood, it converts at each iteration the list of :class:`.Variable`\s into a :class:`.SetOfCavitySettings`.
The latter is given as argument to the :meth:`.BeamCalculator.run_with_this` which gives a :class:`.SimulationOutput` from which the :class:`.Objective`\s are evaluated.
