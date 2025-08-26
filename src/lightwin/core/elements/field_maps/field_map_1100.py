"""Define a field map with 1D rf electro-magnetic field."""

from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.util.typing import EXPORT_PHASES_T


class FieldMap1100(FieldMap):
    """1D rf electro-magnetic field.

    Just inherit from the classic :class:`.FieldMap`; we override the
    ``to_line`` to also update ``k_b`` (keep ``k_e == k_b``).

    """

    def __init__(self, *args, **kwargs) -> None:
        """Init the same object as :class:`.FieldMap100`."""
        return super().__init__(*args, **kwargs)

    def to_line(
        self,
        which_phase: EXPORT_PHASES_T,
        *args,
        inplace: bool = False,
        **kwargs,
    ) -> list[str]:
        r"""Convert the object back into a line in the ``DAT`` file.

        Parameters
        ----------
        which_phase :
            Which phase should be put in the output ``DAT``.
        inplace :
            To modify the :class:`.Element` inplace. The default is False, in
            which case, we return a modified copy.

        Returns
        -------
            The line in the ``DAT``, with updated amplitude and phase from
            current object.

        """
        line = super().to_line(
            which_phase=which_phase, *args, inplace=inplace, **kwargs
        )
        shift = 0
        if self._personalized_name:
            shift += 1
        line[5 + shift] = str(self.cavity_settings.k_e)
        return line
