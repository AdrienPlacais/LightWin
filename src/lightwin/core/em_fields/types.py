"""Define some types to clarify inputs and ouptuts."""

from collections.abc import Callable

#: Describes a 1D position.
Pos1D = float
#: Describes a 2D position.
Pos2D = tuple[float, float]
#: Describes a 3D position.
Pos3D = tuple[float, float, float]
#: Describes a generic position, in any number of dimensions.
PosAnyDim = Pos1D | Pos2D | Pos3D

#: Takes in a position, returns the field spatial component at this position.
FieldFuncComponent = Callable[[PosAnyDim], float]
#: Takes in a 1D position, returns the field spatial component at this
#: position.
FieldFuncComponent1D = Callable[[Pos1D], float]

#: Takes in a position and a phase, returns the field component at this phase
#: and position.
FieldFuncTimedComponent = Callable[[PosAnyDim, float], float]
#: Takes in a position and a phase, returns the complex field component at this
#: phase and position.
FieldFuncComplexTimedComponent = Callable[[PosAnyDim, float], complex]
FieldFuncPhisFit = Callable[[PosAnyDim, float, float], complex]
