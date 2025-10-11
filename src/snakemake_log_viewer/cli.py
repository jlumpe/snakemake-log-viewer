from argparse import ArgumentParser
import logging

from snakemake_logger_plugin_json import models
from snakemake_logger_plugin_json.json import parse_logfile
from .run import RunStatus, JobInfo
from .app import LogfileApp


def load_run(logfile: str) -> RunStatus:

	with open(logfile) as fh:
		records = parse_logfile(fh)

		first = next(records)
		run = RunStatus(started=first.created_dt)
		run.process_record(first)

		for record in records:
			run.process_record(record)

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
