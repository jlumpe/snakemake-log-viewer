from argparse import ArgumentParser
import logging

from snakemake_logger_plugin_json import models
from snakemake_logger_plugin_json.json import parse_logfile
from .run import RunData, JobInfo
from .app import LogfileApp


def debug_on_error():
	import sys

	def handle_error(typ: type[BaseException], value: BaseException, tb):
		import pdbr as pdb
		pdb.post_mortem(tb)

	sys.excepthook = handle_error


def add_fake_logs(logs: list[models.JsonLogRecord], insertat: int) -> None:
	t1 = logs[insertat - 1].created
	t2 = logs[insertat].created

	levels = [logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

	for i, levelno in enumerate(levels):
		levelname = logging.getLevelName(levelno)

		r = (i + 1) / (len(levels) + 1)
		time = r * t2 + (1 - r) * t1

		logs.insert(insertat + i, models.StandardLogRecord(
			levelno=levelno,
			message=f'test {levelname.lower()}',
			created=time,
		))


def load_run(logfile: str) -> RunData:

	with open(logfile) as fh:
		records = parse_logfile(fh)

		first = next(records)
		run = RunData(started=first.created_dt)
		run.process_record(first)

		for record in records:
			run.process_record(record)

	add_fake_logs(run.logs, 5)

	return run


def getapp() -> LogfileApp:
	parser = ArgumentParser()
	parser.add_argument('logfile')
	args = parser.parse_args()

	run = load_run(args.logfile)

	app = LogfileApp(run)
	return app


def main():
	# debug_on_error()
	app = getapp()
	app.run()
