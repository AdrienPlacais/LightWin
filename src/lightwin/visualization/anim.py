"""Define functions to make animated plots.

.. todo::
    discriminate feasible from unfeasible solutions

"""

from collections.abc import Generator

import numpy as np
from matplotlib import animation
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from numpy.typing import NDArray


class AnimatedScatterDesign:
    """An animated scatter plot using matplotlib.animations.FuncAnimation."""

    def __init__(
        self,
        fig: Figure,
        hist: list,
        n_cav: int,
        interval: int = 300,
        blit: bool = True,
        repeat: bool = False,
    ) -> None:
        """Set up and save the animation.

        Parameters
        ----------
        fig :
            The matplotlib figure containing the axes to animate.
        hist :
            History of algorithm states. Each entry must expose a ``.pop``
            attribute with a ``get("X")`` method returning a 2-D array of
            shape ``(n_individuals, 2 * n_cav)``.
        n_cav :
            Number of cavities. The first ``n_cav`` columns of each population
            array are phases; the next ``n_cav`` columns are amplitudes.
        interval :
            Delay between frames in milliseconds.
        blit :
            Whether to use blitting for faster rendering.
        repeat :
            Whether the animation loops after the last frame.

        """
        self.fig = fig
        self.axx = fig.get_axes()
        self.l_scat: list[Artist] = []

        self.numpoints = hist[0].pop.size
        self.n_cav = n_cav
        frames = len(hist) - 1

        self.hist = hist
        self.stream = self.data_stream()

        self.anim = animation.FuncAnimation(
            self.fig,
            self.update,
            interval=interval,
            frames=frames,
            init_func=self.setup_plot,
            blit=blit,
            repeat=repeat,
        )

        writer = animation.ImageMagickWriter(fps=2)
        self.anim.save("anim.gif", writer=writer)

    def setup_plot(self) -> list[Artist]:
        """Initialize drawing of the scatter plot.

        Returns
        -------
            The initial scatter plot artists, one per axis.

        """
        x_ini = next(self.stream)

        for j, axx in enumerate(self.axx):
            x_j = np.column_stack(
                (np.mod(x_ini[:, j], 2.0 * np.pi), x_ini[:, j + self.n_cav])
            )
            self.l_scat.append(
                axx.scatter(x_j[0, :], x_j[1, :], c="r", s=5, alpha=0.5)
            )
        return self.l_scat

    def update(self, frame: int) -> list[Artist]:
        """Update the scatter plots for the given frame.

        Parameters
        ----------
        frame :
            Index of the current animation frame.

        Returns
        -------
            The updated scatter plot artists.

        """
        x_frame = next(self.stream)

        for j, scat in enumerate(self.l_scat):
            x_j = np.column_stack(
                (
                    np.mod(x_frame[:, j], 2.0 * np.pi),
                    x_frame[:, j + self.n_cav],
                )
            )
            scat.set_offsets(x_j)
        return self.l_scat

    def data_stream(self) -> Generator[NDArray[np.float64], None, None]:
        """Yield population arrays for each recorded algorithm state.

        Yields
        ------
            Array of shape ``(n_individuals, 2 * n_cav)`` for each entry in
            :attr:`hist`.

        """
        generator_data = (algo.pop.get("X") for algo in self.hist)
        yield from generator_data
