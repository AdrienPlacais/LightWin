"""Define some types to clarify inputs and ouptuts."""

from collections.abc import Callable

AnyDimInt = int | tuple[int, int] | tuple[int, int, int]
AnyDimFloat = float | tuple[float, float] | tuple[float, float, float]

FieldFuncComponent = Callable[[AnyDimFloat], float]
FieldFuncComponent1D = Callable[[float], float]
FieldFuncTimedComponent = Callable[[AnyDimFloat, float], float]

FieldFuncComplexTimedComponent = Callable[[AnyDimFloat, float], complex]
