"""Define a useless command; raise error as influences the linac design."""

import logging

from lightwin.core.commands.dummy_command import DummyCommand


class SetAdv(DummyCommand):
    """A class that does nothing but raise an error."""

    def __init__(self, *args, **kwargs) -> None:
        """Raise an error."""
        super().__init__(*args, **kwargs)
        logging.info(
            "The SET_ADV is not implemented in LightWin. As this command will "
            "influence the design of the linac, you should set the design and "
            f"comment this command out.\n{self}"
        )
