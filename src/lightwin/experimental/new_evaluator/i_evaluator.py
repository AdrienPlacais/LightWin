"""Define the base object for every evaluator."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.experimental.plotter.i_plotter import IPlotter
from lightwin.experimental.plotter.pd_plotter import PandasPlotter
from lightwin.util.dicts_output import markdown
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T


class IEvaluator(ABC):
    """Base class for all evaluators."""

    #: ``x`` data, used for interpolation and plotting. Generally, ``"z_abs"``
    #: or ``"elt_idx"``.
    _x_quantity: GETTABLE_SIMULATION_OUTPUT_T
    #: Raw ``y`` data; can be modified afterwards by :meth:
    #: `.IEvaluator.post_treat`, *eg* if you want to study relative evolution
    #: of emittance rather than its absolute value.
    _y_quantity: GETTABLE_SIMULATION_OUTPUT_T
    #: kwargs used for plotting.
    _plot_kwargs: dict[str, Any]

    def __init__(
        self, fignum: int, plotter: IPlotter | None = None, **kwargs
    ) -> None:
        """Instantiate the ``plotter`` object."""
        self._fignum = fignum
        self._plotter = plotter if plotter else PandasPlotter()
        if not hasattr(self, "_plot_kwargs"):
            self._plot_kwargs = {}
        self._ref_xdata: NDArray[np.float64]

    def __str__(self) -> str:
        """Give a detailed description of what this class does."""
        return self.__repr__()

    @abstractmethod
    def __repr__(self) -> str:
        """Give a short description of what this class does."""

    @property
    def _markdown(self) -> str:
        """Give a markdown representation of object, with units."""
        return markdown[self._y_quantity]

    @abstractmethod
    def _get(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Get the base data."""
        pass

    def post_treat(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Perform operations on data. By default, return data as is."""
        return raw_df

    def to_pandas(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Give the post-treated data as a pandas dataframe."""
        raise NotImplementedError
        data = self._get(*args, **kwargs)
        post_treated = self.post_treat(data)
        assert isinstance(post_treated, np.ndarray)
        assert hasattr(self, "_ref_xdata")
        as_df = pd.DataFrame(data=post_treated, index=self._ref_xdata)
        return as_df

    @abstractmethod
    def plot(
        self,
        post_treated: Any,
        elts: Sequence[ListOfElements] | None = None,
        png_folders: Sequence[Path] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Plot evaluated data from all the given objects."""
        pass

    def _plot_single(
        self,
        data: Any,
        elts: ListOfElements | None,
        png_path: Path | None = None,
        **kwargs: Any,
    ) -> Any:
        """Plot evaluated data from a single object."""
        return self._plotter.plot(
            data,
            ylabel=self._markdown,
            fignum=self._fignum,
            elts=elts,
            png_path=png_path,
            title=str(self),
            **kwargs,
            **self._plot_kwargs,
        )

    def _plot_complementary(
        self, data: Iterable[float], axes: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Plot other evaluator-specific data."""
        return axes

    @abstractmethod
    def evaluate(
        self, *args: Any, **kwargs: Any
    ) -> tuple[list[bool], pd.DataFrame]:
        """Test if the object(s) under evaluation pass(es) the test.

        Returns
        -------
        list[bool]
            Wether the tests was passed, for every given object.
        pd.DataFrame
            Holds data used for the testing.

        """
        pass
