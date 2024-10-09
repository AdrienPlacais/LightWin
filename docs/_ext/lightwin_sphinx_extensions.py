"""Define a role for easier and more consistent display of units."""

from __future__ import annotations

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxRole
from sphinx.util.typing import ExtensionMetadata


class UnitRole(SphinxRole):
    """A role to display units in math's mathrm format."""

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        text = "".join((r"\mathrm{", f"{self.text}", r"}"))
        node = nodes.math(text=text)
        return [node], []


class PiUnitRole(SphinxRole):
    """A role to display units in math's mathrm format, with a pi first."""

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        text = "".join((r"\pi\mathrm{.", f"{self.text}", r"}"))
        node = nodes.math(text=text)
        return [node], []


def setup(app: Sphinx) -> ExtensionMetadata:
    """Plug new directives into Sphinx."""
    app.add_role("unit", UnitRole())
    app.add_role("piunit", PiUnitRole())

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
