import logging
from typing import ClassVar, NamedTuple, Self, TypeVar, Any, overload
from datetime import timedelta

from snakemake_logger_plugin_json.models import JsonLogRecord


T = TypeVar('T')
T2 = TypeVar('T2')


class Singleton:
	_instance: ClassVar[Self]

	def __init_subclass__(cls) -> None:
		cls._instance = object.__new__(cls)

	def __new__(cls):
		return cls._instance


class Default(Singleton):

	@staticmethod
	def get(value: T | 'Default', default: T) -> T:
		return default if isinstance(value, Default) else value


# ------------------------------------------------------------------------------------------------ #
#                                            Log levels                                            #
# ------------------------------------------------------------------------------------------------ #

class LogLevel(NamedTuple):
	no: int
	name: str
	icon: str


LEVELS = [
	LogLevel(logging.DEBUG,    'debug',    ''),
	LogLevel(logging.INFO,     'info',     ''),
	LogLevel(logging.WARNING,  'warning',  ''),
	LogLevel(logging.ERROR,    'error',    ''),
	LogLevel(logging.CRITICAL, 'critical', ''),
]

LEVELS_DICT = {level.name: level for level in LEVELS}


def get_level_name(record: JsonLogRecord, other: T = None, none: T2 = None) -> str | T | T2:
	if record.levelname is None:
		return none
	name = record.levelname.lower()
	return name if name in LEVELS_DICT else other


# ------------------------------------------------------------------------------------------------ #
#                                               Other                                              #
# ------------------------------------------------------------------------------------------------ #

def split_td(time: timedelta | float) -> tuple[int, int, int, bool]:
	"""Split time delta.

	Parameters
	----------
	time
		Time delta as object or number of seconds

	Returns
	-------
		(hours, minutes, seconds, neg)
	"""
	if isinstance(time, timedelta):
		secs = time.total_seconds()
	else:
		secs = float(time)

	if secs < 0:
		neg = True
		secs = -secs
	else:
		neg = False

	secs = int(secs)
	mins, secs = divmod(secs, 60)
	hours, mins = divmod(mins, 60)

	return hours, mins, secs, neg


@overload
def format_td(td: timedelta | float, none: Any = None) -> str: ...

@overload
def format_td(td: None, none: T = None) -> T: ...

def format_td(td: timedelta | float | None, none: T = None) -> str | T:
	"""Format timedelta to HH:MM:SS."""
	if td is None:
		return none

	hours, mins, secs, neg = split_td(td)

	s = f'{hours:d}:{mins:02d}:{secs:02d}'
	if neg:
		s = '-' + s
	return s
