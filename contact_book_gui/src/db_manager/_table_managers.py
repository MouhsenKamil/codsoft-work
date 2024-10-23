from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData, Column, Text, CheckConstraint, Integer, String


metadata = MetaData()


class Base(DeclarativeBase):
  metadata = metadata


class Contact(Base):
  __tablename__ = "contacts"

  id = Column(Integer, primary_key=True, server_default='1', nullable=False, autoincrement=True)
  name = Column(String(50), nullable=False)
  phone_no = Column(String(15), unique=True)
  email = Column(String(50), nullable=True, unique=True)
  address = Column(Text)

  __table_args__ = (
    CheckConstraint(
      "((phone_no IS NOT NULL) OR (email IS NOT NULL) OR (address IS NOT NULL))",
      name='phone_no_or_email_or_address_is_not_null'
    ),
  )