from pathlib import Path
import pyperclip
import string
import secrets
import inspect
from typing import Any, Callable


def Human_unreadable_urlsafe_password(password_length: int) -> str:
  return secrets.token_urlsafe(password_length)[:password_length]


def Human_unreadable_password_using_printable_characters(password_length: int) -> str:
  return ''.join(secrets.choice(string.printable) for _ in range(password_length))


def XKCD_password_generation_method(num_words: int, delimiter: str = ' ') -> str:
  with open(Path(__file__).parent / 'wordlist.txt') as f:
    wordlist = f.read().split()
    return delimiter.join(secrets.choice(wordlist) for _ in range(num_words))
 

options: list[Callable[[Any], str]] = [
  Human_unreadable_urlsafe_password,
  Human_unreadable_password_using_printable_characters,
  XKCD_password_generation_method
]


def type_based_input[T](
  query: str,
  type_func: type | None = None,
  condn: Callable[[str], T] | None = None,
) -> T:
  MOVE_CURSOR_UP_BY_1_LINE = '\033[1A'
  ERASE_THE_ENTIRE_LINE = '\033[2K'

  if type_func is None:
    type_func = str

  if condn is None:
    condn = lambda x: x

  while True:
    try:
      val = type_func(input(MOVE_CURSOR_UP_BY_1_LINE + ERASE_THE_ENTIRE_LINE + query))
      if condn(val):
        print()
        return val

    except KeyboardInterrupt:
      exit(0)

    except Exception:
      continue


def list_options():
  for idx, opt in enumerate(options, start=1):
    print(f"{idx}. {opt.__name__.replace('_', ' ')}")
  print('\n')

  return type_based_input('Choose the option: ', int, lambda x: 0 < x <= len(options))


def main():
  print('\nPASSWORD GENERATOR')
  print('------------------')

  pass_gen_func = options[list_options() - 1]

  args = []

  pass_gen_func_title = pass_gen_func.__name__.replace('_', ' ')
  print('\n' + pass_gen_func_title + '\n' + '-'*len(pass_gen_func_title), '\n')

  for param_name, param_obj in inspect.signature(pass_gen_func).parameters.items():
    param_type_desc = ''
    if param_obj.annotation != str:
      param_type_desc = f'[{param_obj.annotation.__name__}]'

    args.append(
      type_based_input(
        f"{param_name.replace('_', ' ').title()}{param_type_desc}: ",
        param_obj.annotation
      )
    )

  pyperclip.copy(pass_gen_func(*args))
  print('Password copied to clipboard')


main()
