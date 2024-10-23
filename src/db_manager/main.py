import re
from pathlib import Path
from typing import TypedDict, NoReturn

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from phonenumbers import is_valid_number, is_possible_number, parse as phone_no_parse

from ._table_managers import Base, Contact
from ._formatting import print_err_to_stderr, log_info_to_stdout


EMAIL_REGEX = re.compile(r'^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*|\".+\")@(([a-z\d-]+\.)+[a-z]{2,})|others)$')
file_parent_path = Path(__file__).parent.relative_to(Path().resolve(strict=True))
db_path = file_parent_path.parent.parent / 'db' / 'contacts.db'


class ContactEntry(TypedDict):
  id: int
  name: str
  phone_no: str | None
  email: str | None
  address: str | None


DB_COLUMNS = ['name', 'phone_no', 'email', 'address']
IS_POSSIBLE_PHONE_NUMBER_RE = re.compile(r'^[0-9]{4,12}$')


@print_err_to_stderr
def validator(values: ContactEntry) -> ContactEntry | NoReturn:
  if not values.get('name', ''):
    raise ValueError('Name cannot be empty.')

  email = values.get('email', '').strip()
  phone_no = values.get('phone_no', '').strip()
  address = values.get('address', '').strip()

  if not (phone_no or email or address):
    raise ValueError(
      "Either phone number, email or address is required to add a new entry."
    )

  if email and not EMAIL_REGEX.match(email):
    raise ValueError("The given email address is not valid.")

  phone_no = values.get("phone_no", '').strip()
  if not phone_no:
    return

  try:
    parsed_no = phone_no_parse(phone_no, _check_region=False)

    if not (
      is_valid_number(parsed_no)
      or is_possible_number(parsed_no)
      or IS_POSSIBLE_PHONE_NUMBER_RE.match(phone_no)
    ):
      raise ValueError(phone_no)

  except Exception as e:
    raise ValueError(f"The givem phone number is not valid.") from e

  return values


@print_err_to_stderr
@log_info_to_stdout
def add(values: ContactEntry) -> None:
  validator(values)
  DB_SESSION.add(Contact(**values))


@print_err_to_stderr
@log_info_to_stdout
def search(query: str | None = None) -> list[Contact]:
  sql_query = DB_SESSION.query(Contact)

  if query:
    sql_query = sql_query.filter(
      or_(
        getattr(Contact, attr).ilike(f"%{query}%")
        for attr in ('name', 'phone_no', 'email', 'address')
      )
    )

  return sql_query.all()


@print_err_to_stderr
@log_info_to_stdout
def update(query: ContactEntry, values: ContactEntry) -> None:
  DB_SESSION.query(Contact).filter_by(**query).update(values)


@print_err_to_stderr
@log_info_to_stdout
def delete(query: ContactEntry) -> None:
  DB_SESSION.query(Contact).filter_by(**query).delete()


@print_err_to_stderr
@log_info_to_stdout
def save_changes():
  DB_SESSION.commit()


@print_err_to_stderr
@log_info_to_stdout
def init_db_session():
  global DB_SESSION

  engine = create_engine(f"sqlite:///{db_path}")
  Base.metadata.create_all(bind=engine)

  DB_SESSION = sessionmaker(bind=engine)()
  return DB_SESSION
