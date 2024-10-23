import sys
import typing as t
from functools import wraps

from rich import print as rich_print


P = t.ParamSpec('P')


def print_error(message: str | Exception) -> None:
  if isinstance(message, Exception):
    output = f'{type(message).__name__}: {message}'

  else:
    output = r"\[x] {message}".format(message=message)

  rich_print(f'[red]{output}[/]', file=sys.stderr)


def print_info(message: str) -> None:
  output = r"\[info] {message}".format(message=message)
  rich_print(f'[blue]{output}[/]', file=sys.stderr)



def print_err_to_stderr[F](func: F) -> F:
  @wraps(func)
  def wrapper(*args: P.args, **kwargs: P.kwargs):
    try:
      return func(*args, **kwargs)
    except Exception as e:
      print_error(f'({func.__name__}) {type(e).__name__}: {e}')

  return wrapper


def log_info_to_stdout[F](func: F) -> F:
  @wraps(func)
  def wrapper(*args: P.args, **kwargs: P.kwargs):
    val = func(*args, **kwargs)
    print_info(f'({func.__name__}) {args=}, {kwargs=}, return={val}')
    return val

  return wrapper
