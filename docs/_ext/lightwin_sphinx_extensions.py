"""Define a role for easier and more consistent display of units."""

from __future__ import annotations

from collections import defaultdict
from importlib import import_module
from os import stat
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
        mapping = _load_mapping(self.arguments[0])
        grouped = self._invert_mapping(mapping)

        value_header = self.options.get("value-header", "Value")
        keys_header = self.options.get("keys-header", "Keys")

        return [self._make_table(grouped, value_header, keys_header)]

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

        tgroup += nodes.colspec(colwidth=40)
        tgroup += nodes.colspec(colwidth=60)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for title in (value_header, keys_header):
            header_row += _make_entry(nodes.paragraph(text=title))
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody
        for val, keys in grouped.items():
            tbody += self._make_row(val, keys)

        return table

    def _make_row(self, val: Any, keys: list[str]) -> nodes.row:
        """Make a table row for one value with its keys."""
        row = nodes.row()
        row += _make_entry(
            *_parse_inline_rst(_render(val), self.state, source="configmap")
        )

        keys_text = ", ".join(_render(k) for k in keys)
        row += _make_entry(
            *_parse_inline_rst(keys_text, self.state, source="configmap")
        )
        return row


class ConfigKeysDirective(Directive):
    """Render dictionary keys as a one-column table."""

    required_arguments = 1
    option_spec = {
        "header": directives.unchanged,
        "n_cols": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        mapping = _load_mapping(self.arguments[0])
        keys = list(mapping.keys())
        return [self._make_table(keys, self.options.get("header"))]

    def _make_table(self, keys: list[Any], header: str | None) -> nodes.table:
        """Create a one-column table with keys (optionally with header)."""
        table = nodes.table()

        n_cols = int(self.options.get("n_cols", 1))
        tgroup = nodes.tgroup(cols=n_cols)
        table += tgroup
        for _ in range(n_cols):
            tgroup += nodes.colspec(colwidth=100 / n_cols)

        if header:
            thead = nodes.thead()
            tgroup += thead
            header_row = nodes.row()

            for _ in range(n_cols):
                entry = nodes.entry()
                entry += nodes.paragraph(text=header)
                header_row += entry
            thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody

        n_rows = (len(keys) + n_cols - 1) // n_cols
        for i in range(n_rows):
            this_column_keys = keys[i::n_rows]
            this_column_keys.extend([None] * (n_cols - len(this_column_keys)))
            tbody += self._make_row(this_column_keys)
        return table

    def _make_row(self, keys: list[str | None]) -> nodes.row:
        """Make a table row, can have an arbitrary number of columns."""
        row = nodes.row()
        for k in keys:
            row += [
                _make_entry(
                    *_parse_inline_rst(
                        _render(k), self.state, source="configkeys"
                    )
                )
            ]
        return row


def _parse_inline_rst(text: str, state, source: str) -> list[nodes.Node]:
    """Parse a small ``RST`` fragment into inline nodes."""
    vl = StringList([text], source=source)
    container = nodes.paragraph()
    nested_parse_with_titles(state, vl, container)
    return container.children


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


def _make_entry(*children: nodes.Node) -> nodes.entry:
    """Wrap children in a table entry."""
    entry = nodes.entry()
    entry += list(children)
    return entry


def _render(raw: Any) -> str:
    """Transform an object into a clickable ReST role.

    Specific behaviors according to ``raw`` type:
    - ``None``: return an empty string
    - Class: return class name within the ReST class role
    - Default: return the ``raw.__repr__()`` within backticks.

    """
    if raw is None:
        return ""
    if isinstance(raw, type):
        return f":class:`.{raw.__name__}`"
    # !r to use ``__repr__`` instead of ``__str__``
    return f"``{raw!r}``"


def setup(app: Sphinx) -> ExtensionMetadata:
    """Plug new directives into Sphinx."""
    app.add_role("unit", UnitRole())
    app.add_directive("configmap", ConfigMapDirective)
    app.add_directive("configkeys", ConfigKeysDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
