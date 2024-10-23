"""Define some types to clarify inputs and ouptuts."""

from collections.abc import Callable

AnyDimInt = tuple[int] | tuple[int, int] | tuple[int, int, int]
AnyDimFloat = tuple[float] | tuple[float, float] | tuple[float, float, float]

FieldFuncComponent = Callable[[AnyDimFloat], float]
FieldFuncComponent1D = Callable[[tuple[float]], float]

FieldFuncTimedComponent = Callable[[AnyDimFloat, float], float]
FieldFuncComplexTimedComponent = Callable[[AnyDimFloat, float], complex]
