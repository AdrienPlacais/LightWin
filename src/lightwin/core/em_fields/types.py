"""Define some types to clarify inputs and ouptuts."""

from collections.abc import Callable

Pos1D = float
Pos2D = tuple[float, float]
Pos3D = tuple[float, float, float]
PosAnyDim = Pos1D | Pos2D | Pos3D


FieldFuncComponent = Callable[[PosAnyDim], float]
FieldFuncComponent1D = Callable[[Pos1D], float]

FieldFuncTimedComponent = Callable[[PosAnyDim, float], float]
FieldFuncComplexTimedComponent = Callable[[PosAnyDim, float], complex]
