"""General textual utilities."""

from typing import Any, Never, Iterable, Mapping, TypeAlias, Self, override
from datetime import timedelta

from textual.app import ComposeResult
from textual.widgets import (
	DataTable,
)
from textual.widgets.data_table import RowKey, ColumnKey
from textual.style import Style
from textual.content import Content
from textual.reactive import reactive
from rich.text import Text

from .util import Default


def method_unsupported(*args, **kw) -> Never:
	raise RuntimeError('Method not supported')


# ------------------------------------------------------------------------------------------------ #
#                                              Widgets                                             #
# ------------------------------------------------------------------------------------------------ #

_KVTableItems: TypeAlias = (
	Iterable[tuple[str, object] | tuple[str, object, object]]
	| Mapping[str, object]
)


class KVTable(DataTable):
	"""Table with single column for displaying key-value pairs."""

	colkey: ColumnKey
	default_height: int | None

	def __init__(
		self,
		items: _KVTableItems | None = None,
		*,
		default_height: int | None = None,
		**kw,
	):
		super().__init__(show_header=False, show_cursor=False, **kw)
		self.colkey = super().add_column('Value', key='value')
		self.default_height = default_height

		if items is not None:
			self.add_all(items)

	def add_all(self, items: _KVTableItems):
		"""
		Parameters
		----------
		items
			Iterable of ``(key, value)`` or ``(key, value, label)`` tuples, or mapping. If mapping,
			the values may be ``(value, label)`` pairs.
		"""
		if isinstance(items, Mapping):
			for key, value in items.items():
				if isinstance(value, tuple):
					if len(value) != 2:
						raise ValueError('Mapping values should be 2-tuples')
					value, label = value
					self.add_item(key, value, label)
				else:
					self.add_item(key, value)

		else:
			for item in items:
				if len(item) == 2:
					key, value = item
					label = None
				elif len(item) == 3:
					key, value, label = item
				else:
					raise ValueError('Items must be 2- or 3-tuples')
				self.add_item(key, value, label)

	def add_item(
		self,
		key: str,
		value: Any,
		label: Any = None,
		*,
		height: int | None | Default = Default(),
	) -> RowKey:
		if label is None:
			label = key
		return super().add_row(value, label=label, key=key, height=Default.get(height, self.default_height))

	def update_item(self, key: RowKey | str, value: Any, update_width: bool = False) -> None:
		super().update_cell(key, self.colkey, value, update_width=update_width)

	def remove_item(self, key: RowKey | str) -> None:
		super().remove_row(key)
		self.update_cell

	@override
	def clear(self, columns: bool = False) -> Self:
		if columns:
			raise ValueError('Clearing columns not supported')
		return super().clear()

	add_column = method_unsupported
	add_row = method_unsupported
	update_cell = method_unsupported
	remove_column = method_unsupported
	remove_row = method_unsupported
