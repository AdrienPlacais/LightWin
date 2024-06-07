"""Define an object corresponding to a single line of the ``.dat``."""


class DatLine:
    """Hold a single line of the ``.dat`` file."""

    def __init__(self, line: str, idx: int) -> None:
        """Instantiate the object."""
        self._original_line = line
        self.idx = idx

        personalized_name, weight, splitted = self._strip(line)
        self.splitted = splitted

        if personalized_name:
            self.personalized_name = personalized_name
        if weight:
            self.weight = weight

    def __repr__(self) -> str:
        """Give data used to create current object."""
        return f"#{self.idx:4d} | {self.line}"

    def __str__(self) -> str:
        """Do the same thing as __repr__ for now."""
        return self.__repr__()

    def _strip(self, line: str) -> tuple[str, float, list[str]]:
        """Strip down the line into its essential arguments."""
        name: str
        weight: float
        splitted_line: list[str]
        return name, weight, splitted_line

    @property
    def instruction(self) -> str:
        """Return the command or element name.

        Useful for :class:`.Instruction` instantiation.

        """
        return self.splitted[0]

    @property
    def line(self) -> str:
        """Reconstruct the line (which may have changed since creation)."""
        base = self.splitted
        if weight := getattr(self, "weight", None) is not None:
            base.insert(0, f"({weight})")
        if name := getattr(self, "personalized_name", None) is not None:
            base.insert(0, f"{name}:")
        return " ".join(base)
