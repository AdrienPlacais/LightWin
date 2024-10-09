"""Define a role for easier and more consistent display of units."""

from __future__ import annotations

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxRole
from sphinx.util.typing import ExtensionMetadata


class UnitRole(SphinxRole):
    """A role to display units in math's mathrm format.

    Note that in order to show units such as Ohm, the omega must be escaped
    twice: :unit:`\\Omega`.

    """

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        text = "".join((r"\mathrm{", self.text, r"}"))
        node = nodes.math(text=text)
        return [node], []


def setup(app: Sphinx) -> ExtensionMetadata:
    """Plug new directives into Sphinx."""
    app.add_role("unit", UnitRole())

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
