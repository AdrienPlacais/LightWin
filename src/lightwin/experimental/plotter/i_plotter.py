"""Define the base class for all plotters.

.. todo::
    Remove the ``elts`` argument??

"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any, final

from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.util.dicts_output import markdown
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T


class IPlotter(ABC):
    """The base plotting class."""

    _grid = True
    _sharex = True
    _legend = True
    _structure = True
    _sections = True

    def __init__(self, elts: ListOfElements | None = None) -> None:
        """Instantiate some base attributes."""
        if elts is not None:
            self._elts = elts

    @final
    def plot(
        self,
        data: Any,
        axes: Any | None = None,
        png_path: Path | None = None,
        elts: ListOfElements | None = None,
        fignum: int = 1,
        axes_index: int = 0,
        title: str = "",
        x_axis: GETTABLE_SIMULATION_OUTPUT_T = "z_abs",
        style: Sequence[str] | None = None,
        **plot_kwargs: Any,
    ) -> Any:
        """Plot the provided data.

        Parameters
        ----------
        data :
            Data to be plotted. According to the subclass, it can be a numpy
            array, a pandas dataframe...
        png_path :
            Where the figure will be saved. The default is None, in which case
            figure is not plotted.
        elts :
            Elements to plot if :attr:`_structure` is True. If not provided, we
            take default :attr:`_elts` instead. Note that the colour of the
            failed, compensating, rephased cavities is given by this object.
            The default is None.
        fignum :
            Figure number. The default is 1.
        axes_index :
            Axes identifier. The default is 0, corresponding to the topmost
            sub-axes.
        title :
            Title of the figure.
        plot_kwargs :
            Other keyword arguments passed to the :meth:`_actual_plotting`.

        Returns
        -------
            The created axes object(s).

        """
        new_figure = axes is None

        axes = self._setup_fig(fignum, title) if new_figure else axes

        self._actual_plot(
            data, axes=axes, axes_index=axes_index, style=style, **plot_kwargs
        )

        if self._structure and new_figure:
            if elts is None:
                elts = self._elts
            self._plot_structure(axes, elts, x_axis=x_axis)

        if png_path is not None:
            self.save_figure(axes, png_path)
        return axes

    @abstractmethod
    def _setup_fig(self, fignum: int, title: str, **kwargs) -> Sequence[Any]:
        """Create the figure.

        This method should create the figure with figure number ``fignum``,
        with title ``title``, and eventual keyword arguments. It must return
        one or several axes where data can be plotted.

        """

    @abstractmethod
    def _actual_plot(
        self,
        data: Any,
        ylabel: str,
        axes: Any,
        axes_index: int,
        xlabel: str = markdown["z_abs"],
        style: Sequence[str] | None = None,
        **plot_kwargs: Any,
    ) -> Any:
        """Create the plot itself."""

    @abstractmethod
    def _plot_structure(
        self,
        axes: Any,
        elts: ListOfElements | None = None,
        x_axis: GETTABLE_SIMULATION_OUTPUT_T = "z_abs",
    ) -> None:
        """Add a plot to show the structure of the linac."""
        if elts is None:
            assert hasattr(self, "_elts"), (
                "Please provide at least a defaut ListOfElements for structure"
                " plots."
            )
            elts = self._elts
        if self._sections:
            self._plot_sections(axes, elts, x_axis)

    @abstractmethod
    def _plot_sections(
        self, axes: Any, elts: ListOfElements, x_axis: str
    ) -> None:
        """Add the sections on the structure plot."""

    @abstractmethod
    def save_figure(self, axes: Any, save_path: Path) -> None:
        """Save the created figure."""
