import os
from typing import Any
import dataclasses

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual import containers
from textual import widgets
from textual.widget import Widget
from textual.widgets import (
	Footer, Header, DataTable, TabbedContent, TabPane, Label, Static
)
from textual.style import Style
from textual.content import Content
from textual.reactive import reactive, var
from rich.text import Text
from rich.pretty import Pretty

from snakemake_logger_plugin_json import models
from snakemake_logger_plugin_json.models import JsonLogRecord, SnakemakeLogRecord
from .run import RunData, JobInfo
from .util import LEVELS_DICT, get_level_name, format_td
from .textual import KVTable


# ---------------------------------------------------------------------------- #
#                                  Log screen                                  #
# ---------------------------------------------------------------------------- #

class LogDetails(Vertical):

	rundata: RunData
	record: var[JsonLogRecord | None] = var(None)

	def __init__(self, rundata: RunData):
		super().__init__()
		self.rundata = rundata

	def compose(self) -> ComposeResult:
		yield KVTable(id='log-attrs')
		yield Label('', id='message')
		yield KVTable(id='log-attrs-additional')

	def watch_record(self, record: JsonLogRecord | None) -> None:
		basic_table = self.query_one('#log-attrs', KVTable)
		addl_table = self.query_one('#log-attrs-additional', KVTable)
		message = self.query_one('#message', Label)

		basic_table.clear()
		addl_table.clear()

		if record is None:
			self.border_title = None
			self.set_classes('record-none')
			message.content = ''

		else:
			self.border_title = get_level_name(record, '?', '?').upper()
			self.set_classes([
				'record-' + get_level_name(record, 'other', 'other'),
				'record-' + record.type,
			])
			message.content = record.message or ''

			self._populate_basic(basic_table, record)
			self._populate_addl(addl_table, record)

	def _populate_basic(self, table: KVTable, record: JsonLogRecord) -> None:
		time = record.created_dt - self.rundata.started
		table.add_item('Time', format_td(time))

		event = getattr(record, 'event', None)
		if event is not None:
			table.add_item('Event', str(event))

		if isinstance(record, models.SnakemakeLogRecord):
			jobs = record.associated_jobs()
			if jobs:
				table.add_item('Jobs', ' '.join(map(str, sorted(jobs))))

	def _populate_addl(self, table: KVTable, record: JsonLogRecord) -> None:
		if isinstance(record, models.StandardLogRecord):
			return

		record_fields = set(field.name for field in dataclasses.fields(type(record)))
		base_fields = set(field.name for field in dataclasses.fields(JsonLogRecord))
		fields = record_fields - base_fields
		fields -= {'jobid', 'job_id', 'job_ids', 'jobs'}

		if not fields:
			return None

		for name in fields:
			value = getattr(record, name)
			if isinstance(value, (str, int, bool, os.PathLike)):
				value = str(value)
			elif value is None:
				value = '[dim]None[/]'
			else:
				value = Pretty(value)
			table.add_item(name, value, height=None)


class LogScreen(Horizontal):

	_COLUMNS: list[tuple[str, str, int]] = [
		('time', 'Time', 8),
		('info', 'Info', 4),
		('event', 'Event', 15),
		('message', 'Message', 10),
	]

	BINDINGS = [
		('p', 'toggle_panel()', 'Toggle side panel'),
	]

	rundata: RunData

	def __init__(self, rundata: RunData):
		super().__init__()
		self.rundata = rundata

	def compose(self) -> ComposeResult:
		with Container():
			yield DataTable(
				id='logs-table',
				cursor_type='row',
			)
		yield LogDetails(self.rundata)

	def on_mount(self) -> None:
		table: DataTable = self.query_one('#logs-table', DataTable)
		table.show_horizontal_scrollbar = False

		for key, label, width in self._COLUMNS:
			# table.add_column(label, key=key, width=width)
			table.add_column(label, key=key)

		self._populate_table(table)

	def _populate_table(self, table: DataTable):
		for i, record in enumerate(self.rundata.logs):
			self._add_row(table, record, i)

	def _add_row(self, table: DataTable, record: JsonLogRecord, i: int):
		if record.levelname == 'CRITICAL':
			style = Style.parse('$text-error')
			info = '🛑\uFE0E'
		elif record.levelname == 'ERROR':
			style = Style.parse('$text-error')
			info = '🚫\uFE0E'
		elif record.levelname == 'WARNING':
			style = Style.parse('$text-warning')
			info = '⚠\uFE0E'
		elif record.levelname == 'INFO':
			style = Style()
			# info = 'ℹ\uFE0E'
			info = 'i '
		elif record.levelname == 'DEBUG':
			style = Style.parse('dim')
			# info = '⚙\uFE0E'
			info = 'd '
		else:
			style = Style()
			info = '? '

		event = getattr(record, 'event', None)
		event = Text(event or '', style=style.rich_style)
		time = record.created_dt - self.rundata.started
		time = Text(format_td(time), style=style.rich_style)
		info = Text(info, style=style.rich_style)
		message = Text((record.message or '').strip(), style=style.rich_style, overflow='ellipsis')

		table.add_row(
			time,
			info,
			event,
			message,
			key=str(i),
			# label=str(i),
		)

	def on_data_table_row_highlighted(self, event: DataTable.RowSelected):
		details = self.query_one(LogDetails)
		key = event.row_key.value

		if key is None:
			details.record = None
			return

		try:
			row = int(key)
		except ValueError:
			pass
		else:
			if 0 <= row < len(self.rundata.logs):
				details.record = self.rundata.logs[row]
				return

		details.record = None

	def action_toggle_panel(self) -> None:
		details = self.query_one(LogDetails)
		details.display = not details.display


# ---------------------------------------------------------------------------- #
#                                  Job screen                                  #
# ---------------------------------------------------------------------------- #

class JobDetails(Vertical):

	rundata: RunData
	job: var[JobInfo | None] = var(None)

	def __init__(self, rundata: RunData):
		super().__init__()
		self.rundata = rundata
		self.border_title = 'Job'

	def compose(self) -> ComposeResult:
		yield KVTable(id='job-attrs')

	def watch_job(self, job: JobInfo | None) -> None:
		table = self.query_one('#job-attrs', KVTable)
		table.clear()

		if job is None:
			self.set_classes('job-none')

		else:
			self.set_classes('job-' + job.status)
			self._populate_basic(table, job)

	def _populate_basic(self, table: KVTable, job: JobInfo) -> None:
		table.add_all([
			('id', str(job.id)),
			('rule', job.rule_name),
			('status', job.status),
			('started', '' if job.started is None else format_td(job.started - self.rundata.started)),
			('duration', format_td(job.duration, '')),
		])



class JobsScreen(Horizontal):

	BINDINGS = [
		('p', 'toggle_panel()', 'Toggle side panel'),
	]

	rundata: RunData

	def __init__(self, rundata: RunData):
		super().__init__()
		self.rundata = rundata

	def compose(self) -> ComposeResult:
		yield DataTable(
			cursor_type='row',
		)
		yield JobDetails(self.rundata)

	def on_mount(self) -> None:
		table = self.query_one(DataTable)
		table.add_columns(
			'Rule',
			'Started',
			'Duration',
		)

		self._populate_table(table)

	def _populate_table(self, table: DataTable):
		for job in self.rundata.jobs.values():
			self._add_row(table, job)

	def _add_row(self, table: DataTable, job: JobInfo):
		if job.started:
			started = format_td(job.started - self.rundata.started)
		else:
			started = ''

		if job.started and job.finished:
			duration = format_td(job.finished - job.started)
		else:
			duration = ''

		table.add_row(
			job.rule_name,
			started,
			duration,
			key=str(job.id),
			label=str(job.id),
		)

	def on_data_table_row_highlighted(self, event: DataTable.RowSelected):
		details = self.query_one(JobDetails)
		key = event.row_key.value

		if key is None:
			details.job = None
			return

		try:
			jobid = int(key)
		except ValueError:
			pass
		else:
			if jobid in self.rundata.jobs:
				details.job = self.rundata.jobs[jobid]
				return

		details.job = None

	def action_toggle_panel(self) -> None:
		details = self.query_one(JobDetails)
		details.display = not details.display


# ---------------------------------------------------------------------------- #
#                                      App                                     #
# ---------------------------------------------------------------------------- #

class LogfileApp(App):
	CSS_PATH = 'style.tcss'

	BINDINGS = [
		('l', 'show_tab("log")', 'Log'),
		('j', 'show_tab("jobs")', 'Jobs'),
	]

	rundata: RunData

	def __init__(self, rundata: RunData):
		super().__init__()
		self.rundata = rundata

	def compose(self) -> ComposeResult:
		"""Called to add widgets to the app."""
		yield Header()
		yield Footer()

		with TabbedContent(initial='log'):
			with TabPane('Log', id='log'):
				yield LogScreen(self.rundata)
			with TabPane('Jobs', id='jobs'):
				yield JobsScreen(self.rundata)

	def action_show_tab(self, tabid: str) -> None:
		self.query_one(TabbedContent).active = tabid
