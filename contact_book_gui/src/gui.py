import sys
from functools import wraps
import typing as t

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
  QApplication, QMainWindow, QWidget, QLineEdit, QPushButton, QHeaderView, QVBoxLayout,
  QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView,
)

from PySide6.QtGui import QValidator

from .db_manager import (
  ContactEntry, init_db_session, add, search, update, delete, save_changes, validator,
  DB_COLUMNS
)


class BigLineEdit(QLineEdit):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setMinimumHeight(25)


class StrValidator(QValidator):
  def __init__(
    self, callback: t.Callable[[str, int], bool | t.NoReturn], parent: QObject | None = ...
  ) -> None:
    super().__init__(parent)
    self.callback = callback

  def validate(self, string: str, index: int) -> object:
    if self.callback(string, index):
      valid = QValidator.State.Acceptable
    else:
      valid = QValidator.State.Invalid
    return valid, string, index


class ContactBook(QMainWindow):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Contacts Book")
    self.setGeometry(100, 100, 800, 400)

    # Main layout
    self.main_widget = QWidget()
    self.setCentralWidget(self.main_widget)
    self._layout = QVBoxLayout(self.main_widget)

    # Main menu
    menubar = self.menuBar()
    file_menu = menubar.addMenu('File')

    save_action = file_menu.addAction("Save", self.save_changes_to_db, shortcut="Ctrl+S")
    file_menu.addAction(save_action)

    # Add button
    add_contact_btn = QPushButton("Add")
    add_contact_btn.clicked.connect(self.show_add_contact_fields)

    # Search input
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText('Search')
    search_btn = QPushButton("Search")
    search_btn.clicked.connect(self.search_contact)

    # Delete button
    delete_contact_btn = QPushButton("Delete")
    delete_contact_btn.clicked.connect(self.delete_selected_contacts)

    buttons_layout = QHBoxLayout()
    buttons_layout.addWidget(self.search_input)
    buttons_layout.addWidget(search_btn)
    buttons_layout.addWidget(add_contact_btn)
    buttons_layout.addWidget(delete_contact_btn)

    # Table to display contacts
    self.contact_table = QTableWidget(0, 4)
    self.contact_table.setContentsMargins(0, 0, 0, 0)
    self.contact_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.contact_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    self.contact_table.setHorizontalHeaderLabels(["Name", "Phone", "Email", "Address"])

    self._layout.addLayout(buttons_layout)
    self._layout.addWidget(self.contact_table)

    # Hidden input fields for adding/updating contacts
    self.name_input = BigLineEdit()
    self.name_input.setPlaceholderText('Name')

    self.phone_input = BigLineEdit()
    self.phone_input.setPlaceholderText('Phone')

    self.email_input = BigLineEdit()
    self.email_input.setPlaceholderText('Email')

    self.address_input = BigLineEdit()
    self.address_input.setPlaceholderText('Address')

    save_btn = QPushButton("Save")
    save_btn.clicked.connect(self.add_contact_from_input_entries)

    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(self.hide_add_contact_fields)

    add_contact_dialog_buttons_layout = QHBoxLayout()
    add_contact_dialog_buttons_layout.addWidget(save_btn)
    add_contact_dialog_buttons_layout.addWidget(cancel_btn)

    name_layout = QHBoxLayout()
    name_layout.addWidget(self.name_input)

    phone_no_layout = QHBoxLayout()
    phone_no_layout.addWidget(self.phone_input)

    email_layout = QHBoxLayout()
    email_layout.addWidget(self.email_input)

    address_layout = QHBoxLayout()
    address_layout.addWidget(self.address_input)

    self.input_fields = QWidget()

    LR_PADDING = 150
    UD_PADDING = 10

    input_layout = QVBoxLayout()
    input_layout.setContentsMargins(LR_PADDING, UD_PADDING, LR_PADDING, UD_PADDING)
    input_layout.setSpacing(10)

    input_layout.addLayout(name_layout)
    input_layout.addLayout(phone_no_layout)
    input_layout.addLayout(email_layout)
    input_layout.addLayout(address_layout)
    input_layout.addLayout(add_contact_dialog_buttons_layout)

    self.input_fields.setLayout(input_layout)
    self._layout.addWidget(self.input_fields)
    self.input_fields.hide()

    self.recent_changes: dict[int, ContactEntry] = {}
    self.contact_table.itemChanged.connect(self.update_local_changes_cache)
    self.db_session = init_db_session()
    self.load_db()

  def display_err_as_critical[F](func: F) -> F:
    @wraps(func)
    def wrapper(self, *args, **kwargs):
      try:
        return func(self, *args, **kwargs)

      except Exception as e:
        QMessageBox.critical(self, "Error", f"{type(e).__name__}: {e}")

    return wrapper

  def delete_selected_contacts(self) -> None:
    selected_items = self.contact_table.selectedItems()
    if not selected_items:
      QMessageBox.warning(self, "Error", "No contacts selected to delete.")
      return

    rows_to_delete = {item.row() for item in selected_items}

    for row in sorted(rows_to_delete, reverse=True):
      self.contact_table.removeRow(row)
      if row in self.recent_changes:
        delete()

    QMessageBox.information(self, "Info", "Selected contacts have been deleted.")

  def update_local_changes_cache(self, item: QTableWidgetItem) -> None:
    self.recent_changes[item.row()][DB_COLUMNS[item.column()]] = item.text()

  def show_add_contact_fields(self):
    self.input_fields.show()

  def hide_add_contact_fields(self):
    self.input_fields.hide()

  @display_err_as_critical
  def add_contact(
    self, name: str, phone_no: str | None = None, email: str | None = None, address: str | None = None
  ) -> None:
    validator({'name': name, 'phone_no': phone_no, 'email': email, 'address': address})

    row_position = self.contact_table.rowCount()
    self.contact_table.insertRow(row_position)
    self.contact_table.setItem(row_position, 0, QTableWidgetItem(name))
    self.contact_table.setItem(row_position, 1, QTableWidgetItem(phone_no))
    self.contact_table.setItem(row_position, 2, QTableWidgetItem(email))
    self.contact_table.setItem(row_position, 3, QTableWidgetItem(address))

    add({"name": name, "phone_no": phone_no, "email": email, "address": address})

  def add_contact_from_input_entries(self):
    name = self.name_input.text()
    phone = self.phone_input.text()
    email = self.email_input.text()
    address = self.address_input.text()

    if not name:
      QMessageBox.warning(self, "Error", "Name cannot be empty.")
      return

    if not (phone or email or address):
      QMessageBox.warning(
        self, "Error", "Either phone number, email or address is required to add a new entry."
      )
      return

    self.add_contact(name, phone, email, address)

    self.name_input.clear()
    self.phone_input.clear()
    self.email_input.clear()
    self.address_input.clear()
    self.hide_add_contact_fields()

  def search_contact(self):
    query = self.search_input.text().lower()
    found = False

    if not query:
      return

    for row in range(self.contact_table.rowCount()):
      match = False
      for col in range(self.contact_table.columnCount()):
        item = self.contact_table.item(row, col)
        if item and query in item.text().lower():
          match = True
          break

      if match:
        self.contact_table.selectRow(row)
        found = True
        break

    if not found:
      QMessageBox.information(self, "Not Found", "No contact found matching the query.")

    else:
      QMessageBox.warning(self, "Input Error", "Please enter a search query.")

  def load_db(self):
    for contact in search():
      self.add_contact(
        name=contact.name, phone_no=contact.phone_no, address=contact.address, email=contact.email
      )

  # def refresh_table_contents(self):
  #   ...

  def delete_selected_contact(self):
    current_row = self.contact_table.currentRow()

    if current_row != -1:
      self.contact_table.removeRow(current_row)

    else:
      QMessageBox.warning(self, "Delete Error", "No contact selected to delete.")

  def save_changes_to_db(self):
    if self.recent_changes:
      for contact in self.recent_changes.values():
        update(contact['phone_no'], contact)

      self.recent_changes = {}

    save_changes()


def run():
  app = QApplication(sys.argv)
  window = ContactBook()
  window.show()
  sys.exit(app.exec())
