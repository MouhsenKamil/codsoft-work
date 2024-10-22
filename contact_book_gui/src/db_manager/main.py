import re
from pathlib import Path
from typing import TypedDict, NoReturn

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from phonenumbers import is_valid_number, is_possible_number, parse as phone_no_parse

from ._table_managers import Base, Contact
from ._formatting import print_err_to_stderr


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
  email = values.get('email', None)
  if email is not None and not EMAIL_REGEX.match(email):
    raise ValueError("Not a valid email address.")

  phone_no = values.get("phone_no", None)
  if phone_no is None:
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
    raise ValueError(f"Not a valid phone number.") from e

  return values


@print_err_to_stderr
def add(values: ContactEntry) -> None:
  validator(values)
  DB_SESSION.add(Contact(**values))
  # DB_SESSION.commit()


@print_err_to_stderr
def search(query: str | None = None) -> list[Contact]:
  # return DB_SESSION.execute(text(
  #     "SELECT * FROM contacts WHERE name LIKE :name OR phone_no LIKE :phone_no OR email LIKE :email OR address LIKE :address",
  #   ), dict.fromkeys(('name', 'phone_no', 'email', 'address'), f"%{query}%"),
  # ).all()

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
def update(query: ContactEntry, values: ContactEntry) -> None:
  if isinstance(phone_nos, int):
    phone_nos = (phone_nos,)

  DB_SESSION.query(Contact).filter_by(**query).update(values)
  # DB_SESSION.commit()


@print_err_to_stderr
def delete(query: ContactEntry) -> None:
  if isinstance(phone_nos, int):
    phone_nos = (phone_nos,)

  DB_SESSION.query(Contact).filter_by(**query).delete()
  # DB_SESSION.commit()

@print_err_to_stderr
def save_changes():
  DB_SESSION.commit()


def init_db_session():
  global DB_SESSION

  engine = create_engine(f"sqlite:///{db_path}")
  Base.metadata.create_all(bind=engine)

  DB_SESSION = sessionmaker(bind=engine)()
  # print(*(vars(i) for i in search(query='rma')))
  return DB_SESSION


# if __name__ == "__main__":
#   init_db_session()
