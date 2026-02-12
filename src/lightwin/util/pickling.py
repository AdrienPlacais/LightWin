"""Define a class to pickle objects.

"pickling" a file comes down to saving it in binary format. It can be loaded
and used again later, even with a different Python instance. This is useful
when you want to study a :class:`.Fault` that took a long time to be
compensated, or a :class:`.SimulationOutput` obtained by a time-consuming
TraceWin multiparticle simulation.

.. warning::
    This a very basic pickling. Do not use for long-term storage, but for debug
    only.

.. note::
    Some attributes such as lambda function in :class:`.FieldMap` or modules in
    :class:`.SimulationOutput` cannot be pickled by the built-in `pickle`
    module. I do not plan to refactor them, so for now we stick with
    `cloudpickle` module.

Some objects have built-in `pickle` and `unpickle` methods, namely:

    - :class:`.Accelerator`
    - :class:`.Fault`
    - :class:`.FaultScenario`
    - :class:`.ListOfElements`
    - :class:`.SimulationOutput`

"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type, TypeVar, overload

T = TypeVar("T")


class MyPickler(ABC):
    """Define an object that can save/load arbitrary objects to files."""

    @abstractmethod
    def pickle(
        self,
        my_object: object,
        path: Path | str | None,
        initialfile: Path | str | None = None,
        initialdir: Path | str | None = None,
        title: str | None = None,
    ) -> Path | None:
        """Pickle ("save") the object to a binary file."""
        pass

    @overload
    def unpickle(
        self,
        path: Path | str | None,
        expected: None,
        title: str | None = None,
    ) -> object | None: ...
    @overload
    def unpickle(
        self,
        path: Path | str | None,
        expected: Type[T],
        title: str | None = None,
    ) -> T | None: ...

    @abstractmethod
    def unpickle(
        self,
        path: Path | str | None,
        expected: type | None = None,
        title: str | None = None,
    ) -> object | None:
        """Unpickle ("load") the given path to recreate original object."""
        pass


class MyCloudPickler(MyPickler):
    """A :class:`.MyPickler` that can handle modules and lambda functions.

    This pickler should not raise errors, but all attributes may not be
    properly re-created.

    """

    def __init__(self) -> None:
        """Check that `cloudpickle` module can be imported."""
        try:
            import cloudpickle
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "cloudpickler module not found. This optional module is "
                "mandatory for the pickler `MyCloudPickler` to work."
            ) from e

        self._cloudpickle = cloudpickle

    def pickle(
        self,
        my_object: object,
        path: Path | str | None,
        initialfile: Path | str | None = None,
        initialdir: Path | str | None = None,
        title: str | None = None,
    ) -> Path | None:
        """Pickle ("save") the object to a binary file.

        Parameters
        ----------
        my_object :
            Object to pickle.
        path :
            Filepath to the pickled object. If ``None``, a GUI dialog will
            prompt the user to select a file.
        initialdir :
            The directory that the GUI dialog starts in, when ``path`` is
            ``None``.
        initialfile :
            The file selected upon opening the GUI dialog, when ``path`` is
            ``None``.
        title :
            Title of the GUI window. Use this to clarify what should be
            pickled.

        Returns
        -------
        Absolute path to the pickled object, or ``None`` if no object was
        pickled.

        """

        if path is None:
            if initialfile is None:
                initialfile = my_object.__class__.__name__ + ".pkl"

            path = ask_pickle_filename(
                initialfile=initialfile,
                initialdir=initialdir,
                title=title
                or f"Choose where the {my_object.__class__} should be pickled "
                "(saved).",
            )
        else:
            path = Path(path).resolve().absolute()
        if path is None:
            logging.error(
                "You provided `path = None`, so I will skip the pickling of "
                f"{my_object = }."
            )
            return

        with open(path, "wb") as f:
            self._cloudpickle.dump(my_object, f)

        logging.info(f"Pickled {my_object} to {path}.")
        return path

    def unpickle(
        self,
        path: Path | str | None,
        expected: type | None = None,
        title: str | None = None,
    ) -> object | None:
        """Unpickle ("load") the given path to recreate original object.

        Parameters
        ----------
        path :
            Filepath to the pickled object. If ``None``, a GUI dialog will
            prompt the user to select a file.
        expected :
            Expected type of the unpickled object. If provided, the method will
            check if the unpickled object is an instance of ``expected``. If
            not, a ``TypeError`` is raised.
        title :
            Title of the GUI window. Use this to clarify what should be
            unpickled.

        Returns
        -------
        Unpickled object. Has type ``expected`` if this argument was provided.
        If there was a problem, ``None`` is returned but no exception is
        raised.

        """
        if path is None:
            info = "object"
            if expected:
                info = str(expected)
            path = ask_pickle_filename(
                title=title
                or f"Choose which {info} should be unpickled (loaded).",
            )
        if path is None:
            logging.error(
                "You provided `path = None`, so I do not have anything to "
                "unpickle."
            )
            return
        with open(path, "rb") as f:
            my_object = self._cloudpickle.load(f)
        if expected is not None and not isinstance(my_object, expected):
            raise TypeError(f"Expected {expected}, got {type(my_object)}")
        return my_object


def ask_pickle_filename(
    initialdir: Path | str | None = None,
    initialfile: Path | str | None = None,
    title: str = "Choose pickle filename",
) -> Path | None:
    """Open a GUI dialog to choose the pickle filename.

    Parameters
    ----------
    initialdir :
        The directory that the dialog starts in.
    initialfile :
        The file selected upon opening the dialog.

    Returns
    -------
    Absolute filepath of pickle file to load/save. If None is returned, the
    pickling operation will simply be skipped.

    """
    try:
        from tkinter import Tk
        from tkinter.filedialog import asksaveasfilename
    except ModuleNotFoundError:
        logging.error(
            "tkinter module is mandatory for the GUI file explorer to work, "
            "but it was not found. Skipping the associated pickling operation."
        )
        return

    root = Tk()
    root.withdraw()  # Hide the root window

    if initialdir:
        Path(initialdir).mkdir(parents=True, exist_ok=True)

    filepath = asksaveasfilename(
        title=title,
        initialdir=initialdir,
        initialfile=initialfile,
        defaultextension=".pkl",
        filetypes=[("Pickle files", "*.pkl")],
    )
    root.destroy()

    if not filepath:
        logging.info("No filepath was set, will skip pickling.")
        return
    return Path(filepath).resolve().absolute()
