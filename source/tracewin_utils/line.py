"""Define an object corresponding to a single line of the ``.dat``."""

import re
from collections.abc import Collection


def _split_named_elements(elements: Collection[str]) -> list[str]:
    """Split elements into named and unnamed components."""
    result = []
    named_element_pattern = re.compile(r"^([\w-]+)\s*:\s*(.+)$")
    for element in elements:
        match = named_element_pattern.match(element)
        if match:
            name, rest = match.groups()
            result.append(name)
            result.extend(rest.split())
        else:
            result.extend(element.split())
    return result


def _split_weighted_elements(elements: list[str]) -> list[str]:
    """Split elements with weights."""
    result = []
    weighted_element_pattern = re.compile(r"^(\w+)\s*(\(.*\))?$")
    for element in elements:
        match = weighted_element_pattern.match(element)
        if match:
            name, weight = match.groups()
            result.append(name)
            if weight:
                result.append(weight)
        else:
            result.append(element)
    return result


def slice_dat_line(line: str) -> list[str]:
    """Parse a line from a .dat file into meaningful parts."""
    line = line.strip()
    if not line:
        return []

    if line.startswith(";"):
        return [";", line[1:].strip()]

    if ";" in line:
        line = line.split(";", 1)[0].strip()

    elements = line.split()
    elements = _split_named_elements(elements)
    elements = _split_weighted_elements(elements)

    return elements


def _is_a_path_instruction(line: str) -> bool:
    """Detect if this is a path instruction."""
    path_instructions = ("FIELD_MAP_PATH",)
    splitted = line.split()
    if len(splitted) == 0:
        return False
    for instruction in path_instructions:
        if splitted[0].casefold() == instruction.casefold():
            return True
    return False


class DatLine:
    """Hold a single line of the ``.dat`` file."""

    def __init__(self, line: str, idx: int) -> None:
        """Instantiate the object."""
        self._original_line = line
        self.idx = idx

        self.personalized_name: str | None = None
        self.weight: float | None = None
        self.splitted = []

        self._parse_line(line)

    def __repr__(self) -> str:
        """Give data used to create current object."""
        return f"#{self.idx:4d} | {self.line}"

    def __str__(self) -> str:
        """Do the same thing as __repr__ for now."""
        return self.__repr__()

    def _parse_line(self, line: str) -> None:
        """Parse the line into its components."""
        if _is_a_path_instruction(line):
            self.splitted = line.split(maxsplit=1)
            return

        elements = slice_dat_line(line)
        if len(elements) == 0:
            return
        # Check for a personalized name
        name_colon_index = elements[0].find(":")
        if name_colon_index != -1:
            self.personalized_name = elements.pop(0).strip(":")

        if elements[1] == ":":
            del elements[1]
            self.personalized_name = elements.pop(0)

        # Check for weight
        if elements[1].startswith("(") and elements[1].endswith(")"):
            self.weight = float(elements.pop(1).strip(")").strip("("))

        self.splitted = elements

    @property
    def instruction(self) -> str:
        """Return the command or element name.

        Useful for :class:`.Instruction` instantiation.

        """
        return self.splitted[0] if self.splitted else ""

    @property
    def line(self) -> str:
        """Reconstruct the line (which may have changed since creation)."""
        base = self.splitted[:]
        if self.weight is not None:
            base.insert(0, str(self.weight))
        if self.personalized_name is not None:
            base.insert(0, f"{self.personalized_name}:")
        return " ".join(base)


# Example usage
if __name__ == "__main__":
    line = "Michel : DRIFT 76"
    dat_line = DatLine(line, -1)
    print(f"name = {dat_line.personalized_name}")
    print(f"weight = {dat_line.weight}")
    print(f"instruc = {dat_line.instruction}")
    print(f"line = {dat_line.line}")
    print(f"splitted = {dat_line.splitted}")
