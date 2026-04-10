"""Define a class to store several |CS|.

.. todo::
    I should create a :class:`.SetOfCavitySettings` with
    |CS| for every cavity of the compensation zone. Mandatory to recompute the
    synchronous phases.

"""

from collections.abc import Collection, Mapping, Sequence
from typing import Literal, Self, TypeVar

from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.util.typing import (
    CONCATENABLE_CAVITY_SETTINGS,
    OPTIMIZATION_STATUS,
)

FieldMap = TypeVar("FieldMap")


class SetOfCavitySettings(dict[FieldMap, CavitySettings]):
    """Hold several cavity settings, to try during optimisation process."""

    def __init__(
        self, several_cavity_settings: dict[FieldMap, CavitySettings]
    ) -> None:
        """Create the proper dictionary."""
        super().__init__(several_cavity_settings)
        self._ordered_cav, self._ordered_settings = self._order()

    def __getattr__(self, key: str) -> list[float]:
        """Override the default ``getattr`` to access some quantities.

        .. note::
            ``__getattr__`` is called after the ``__get_attribute__`` method,
            when the latter did not lead to a valid output.

        .. todo::
            Add ``CONCATENABLE_CAVITY_SETTINGS`` to the __dir__. Also,
            may set this tuple from CavitySettings.__class__.__dir__ or
            something.

        """
        if key not in CONCATENABLE_CAVITY_SETTINGS:
            raise AttributeError(
                f"{key = } not in {CONCATENABLE_CAVITY_SETTINGS = }"
            )

        return [getattr(settings, key) for settings in self._ordered_settings]

    def __dir__(self) -> Sequence[str]:
        """Return the stored variables and some of |CS|."""
        return sorted(dir(self.__class__) + list(CONCATENABLE_CAVITY_SETTINGS))

    @classmethod
    def from_incomplete_set(
        cls,
        compensating_cavity_settings: Mapping[FieldMap, CavitySettings] | None,
        cavities: Collection[FieldMap],
        optimization_status: OPTIMIZATION_STATUS,
    ) -> Self:
        """Create an object with settings for all the field maps.

        We give each cavity settings from ``set_of_cavity_settings`` if they
        are listed in this object. If they are not, we give them their default
        |CS| (`FieldMap.cavity_settings` attribute). This method is used to
        generate |SO| where all the cavity settings are explicitly defined.

        .. note::
            In fact, may be useless. In the future, the nominal cavities will
            also have their own |CS| in the compensation zone.

        Parameters
        ----------
        compensating_cavity_settings :
            Maps compensating cavities to their compensation settings.
        cavities :
            All cavities that should have a |CS| (typically, all the cavities
            in a sub-|LOE| studied during an optimisation process).
        optimization_status :
            Used when ``cavity`` is not in ``cavity_settings`` (*ie*, when the
            cavity is not a compensating cavity). During optimization, we
            return a copy of its |CS| to avoid altering the original. When
            optimization is over, we return the original to set it's final
            ``phi_s``, ``phi_0_rel``, ``phi_rf``, etc.

        Returns
        -------
            Settings for all cavities in ``cavities``.

        """
        complete_set_of_settings = {
            cavity: _get_settings(
                cavity,
                compensating_cavity_settings or SetOfCavitySettings({}),
                optimization_status,
            )
            for cavity in cavities
        }
        return cls(complete_set_of_settings)

    @classmethod
    def nominal(cls, elements: Collection[Element]) -> Self:
        """Get |CS| from objects."""
        settings = {
            cav: settings
            for cav in elements
            if (settings := getattr(cav, "cavity_settings", None)) is not None
        }
        return cls(settings)

    def re_set_elements_index_to_absolute_value(self) -> None:
        """Update cavities index to properly set `ele[n][v]` commands.

        When switching from a sub-|LOE| during the optimisation process to the
        full |LOE| after the optimisation, we must update index ``n`` in the
        ``ele[n][v]]`` command.

        """
        for cavity, setting in self.items():
            absolute_index = cavity.idx["elt_idx"]
            setting.index = absolute_index

    def _order(self) -> tuple[Sequence[FieldMap], Sequence[CavitySettings]]:
        """Return all the |E| in ``self`` in good order."""
        ordered_cav = sorted(self.keys(), key=lambda cav: cav.idx["elt_idx"])
        ordered_settings = [self[cav] for cav in ordered_cav]
        return ordered_cav, ordered_settings


def _get_settings(
    cavity: FieldMap,
    compensating_cavity_settings: Mapping[FieldMap, CavitySettings],
    optimization_status: OPTIMIZATION_STATUS,
) -> CavitySettings:
    """Take the settings from the set of settings if possible.

    If ``cavity`` is not listed in ``set_of_cavity_settings``, take its nominal
    |CS| instead.

    Parameters
    ----------
    cavity :
        Cavity for which you want settings.
    set_of_cavity_settings :
        Different cavity settings (a priori given by an
        :class:`.OptimisationAlgorithm`), or an empty dict.
    optimization_status :
        Used when ``cavity`` is not in ``cavity_settings`` (*ie*, when the
        cavity is not a compensating cavity). During optimization, we return a
        copy of its |CS| to avoid altering the original.
        When optimization is over, we return the original to set it's final
        ``phi_s``, ``phi_0_rel``, ``phi_rf``, etc.

    Returns
    -------
        Cavity settings for ``cavity``.

    """
    if cavity in compensating_cavity_settings:
        return compensating_cavity_settings[cavity]

    settings = cavity.cavity_settings

    if optimization_status == "in progress":
        new_settings = CavitySettings.copy(settings, info="getter")
        return new_settings
    if optimization_status == "finished":
        return settings
    return ValueError(f"{optimization_status = } not understood")
