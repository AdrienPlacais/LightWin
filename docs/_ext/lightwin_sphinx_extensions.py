"""Define a role for easier and more consistent display of units."""

from __future__ import annotations

from collections import defaultdict
from importlib import import_module
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxRole
from sphinx.util.nodes import nested_parse_with_titles
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


class ConfigMapDirective(Directive):
    """A directive to display key-value pairs, value beeing a class role."""

    required_arguments = 1
    option_spec = {
        "value-header": directives.unchanged,
        "keys-header": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        mapping = self._load_mapping(self.arguments[0])
        grouped = self._invert_mapping(mapping)

        value_header = self.options.get("value-header", "Value")
        keys_header = self.options.get("keys-header", "Keys")

        return [self._make_table(grouped, value_header, keys_header)]

    @staticmethod
    def _load_mapping(dotted_path: str) -> dict[str, Any]:
        """Import and return the dictionary given by dotted path."""
        module_path, _, attr_name = dotted_path.rpartition(".")
        if not module_path:
            raise ValueError(f"Invalid path: {dotted_path}")

        module = import_module(module_path)
        mapping = getattr(module, attr_name)
        if not isinstance(mapping, dict):
            raise TypeError(f"{dotted_path} is not a dictionary")

        return mapping

    @staticmethod
    def _invert_mapping(mapping: dict[str, Any]) -> dict[Any, list[str]]:
        """Group keys by their values."""
        grouped: dict[Any, list[str]] = defaultdict(list)
        for key, val in mapping.items():
            grouped[val].append(key)
        return grouped

    def _make_table(
        self,
        grouped: dict[Any, list[str]],
        value_header: str,
        keys_header: str,
    ) -> nodes.table:
        """Create a two-column table (value | keys)."""
        table = nodes.table()
        tgroup = nodes.tgroup(cols=2)
        table += tgroup

        # Column specs
        tgroup += nodes.colspec(colwidth=40)
        tgroup += nodes.colspec(colwidth=60)

        # Header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for title in (value_header, keys_header):
            header_row += self._make_entry(nodes.paragraph(text=title))
        thead += header_row

        # Body
        tbody = nodes.tbody()
        tgroup += tbody
        for val, keys in grouped.items():
            tbody += self._make_row(val, keys)

        return table

    def _make_row(self, val: Any, keys: list[str]) -> nodes.row:
        """Make a table row for one value with its keys."""
        row = nodes.row()

        if isinstance(val, type):
            rendered_val = f":class:`.{val.__name__}`"
        else:
            rendered_val = f"``{val!r}``"
        row += self._make_entry(*parse_inline_rst(rendered_val, self.state))

        keys_text = ", ".join(f"``{k}``" for k in keys)
        row += self._make_entry(*parse_inline_rst(keys_text, self.state))
        return row

    @staticmethod
    def _make_entry(*children: nodes.Node) -> nodes.entry:
        """Wrap children in a table entry."""
        entry = nodes.entry()
        entry += list(children)
        return entry


def parse_inline_rst(text: str, state, lineno: int = 0):
    """Parse a small ``RST`` fragment into inline nodes."""
    vl = StringList([text], source="configmap")
    # vl.append(text, source="(configmap)", offset=lineno)
    container = nodes.paragraph()
    nested_parse_with_titles(state, vl, container)
    return container.children


def setup(app: Sphinx) -> ExtensionMetadata:
    """Plug new directives into Sphinx."""
    app.add_role("unit", UnitRole())
    app.add_directive("configmap", ConfigMapDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
