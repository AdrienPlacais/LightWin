"""Define a plotter that rely on the pandas plotting methods.

.. todo::
    Maybe should inherit from MatplotlibPlotter?

"""

from lightwin.experimental.plotter.matplotlib_plotter import MatplotlibPlotter


class PandasPlotter(MatplotlibPlotter):
    """A plotter that takes in pandas dataframe."""
