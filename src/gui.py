import sys
from functools import wraps
import typing as t

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
  QApplication, QMainWindow, QWidget, QLineEdit, QPushButton, QHeaderView, QVBoxLayout,
  QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView,
  QLabel, QDialog
)

from .db_manager import (
  ContactEntry, init_db_session, add, search, update, delete, save_changes, validator,
  DB_COLUMNS
)


class BigLineEdit(QLineEdit):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setMinimumHeight(25)


class AddContactDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)

    self.setWindowTitle("Add New Contact")
    self.setGeometry(100, 100, 300, 200)

    layout = QVBoxLayout()

    # Name field
    self.name_input = BigLineEdit()
    self.name_input.setPlaceholderText('Name')
    self.name_input.textChanged.connect(self.clear_err_msg)

    # Phone field
    self.phone_input = BigLineEdit()
    self.phone_input.setPlaceholderText('Phone')
    self.phone_input.textChanged.connect(self.clear_err_msg)

    # Email field
    self.email_input = BigLineEdit()
    self.email_input.setPlaceholderText('Email')
    self.email_input.textChanged.connect(self.clear_err_msg)

    # Address field
    self.address_input = BigLineEdit()
    self.address_input.setPlaceholderText('Address')
    self.address_input.textChanged.connect(self.clear_err_msg)

    # Error msg field
    self.err_text_field = QLabel('')

    # Buttons
    self.save_button = QPushButton("Save")
    self.save_button.clicked.connect(self.add_contact)
    self.cancel_button = QPushButton("Cancel")
    self.cancel_button.clicked.connect(self.reject)

    # Layout for input fields and buttons
    form_layout = QVBoxLayout()
    form_layout.addWidget(self.name_input)
    form_layout.addWidget(self.phone_input)
    form_layout.addWidget(self.email_input)
    form_layout.addWidget(self.address_input)
    form_layout.addWidget(self.err_text_field)

    button_layout = QHBoxLayout()
    button_layout.addWidget(self.save_button)
    button_layout.addWidget(self.cancel_button)

    layout.addLayout(form_layout)
    layout.addLayout(button_layout)

    self.setLayout(layout)

  def set_err_msg(self, msg: str) -> None:
    self.err_text_field.setText(msg)

  def clear_err_msg(self):
    if self.err_text_field.text():
      self.set_err_msg("")

  def add_contact(self) -> None:
    name = self.name_input.text()
    phone_no = self.phone_input.text()
    email = self.email_input.text()
    address = self.address_input.text()

    try:
      validator({'name': name, 'phone_no': phone_no, 'email': email, 'address': address})

    except Exception as e:
      self.set_err_msg(str(e))
      return

    self.parent().add_contact(name, phone_no, email, address, True)

    name = self.name_input.clear()
    phone_no = self.phone_input.clear()
    email = self.email_input.clear()
    address = self.address_input.clear()

    self.hide()


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
    self.search_input.returnPressed.connect(self.search_contact)
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

    self.input_fields = AddContactDialog(self)
    self.input_fields.hide()

    self.local_changes: dict[int, ContactEntry] = {}
    self.local_deletion_changes: set[int] = set()
    self.db_session = init_db_session()
    self.load_db()
    self.contact_table.itemChanged.connect(self.update_local_changes_cache)

    self.showing_search_results: bool = False

  def display_err_as_critical[F](func: F) -> F:
    @wraps(func)
    def wrapper(self, *args, **kwargs):
      try:
        return func(self, *args, **kwargs)

      except Exception as e:
        QMessageBox.critical(self, "Error", f"{type(e).__name__}: {e}")

    return wrapper

  @display_err_as_critical
  def delete_selected_contacts(self) -> None:
    selected_items = self.contact_table.selectedItems()
    if not selected_items:
      QMessageBox.warning(self, "Error", "No contacts selected to delete.")
      return

    rows_to_delete = {item.row() for item in selected_items}

    for row in sorted(rows_to_delete, reverse=True):
      self.add_local_deletion_changes_cache(row)
      self.contact_table.removeRow(row)

    QMessageBox.information(self, "Info", "Selected contacts have been deleted.")

  @display_err_as_critical
  def update_local_changes_cache(self, item: QTableWidgetItem) -> None:
    row = self.contact_table.item(item.row(), 0).data(Qt.UserRole)
    self.local_changes.setdefault(row, {})[DB_COLUMNS[item.column()]] = item.text()

  @display_err_as_critical
  def add_local_deletion_changes_cache(self, row_id: int) -> None:
    row = self.contact_table.item(row_id, 0).data(Qt.UserRole)
    self.local_deletion_changes.add(row)

  def show_add_contact_fields(self):
    self.input_fields.show()

  def hide_add_contact_fields(self):
    self.input_fields.hide()

  @display_err_as_critical
  def add_contact(
    self,
    name: str,
    phone_no: str = '',
    email: str = '',
    address: str = '',
    update_db: bool = False,
    _id: int = -1,
  ) -> None:
    row_position = self.contact_table.rowCount()
    self.contact_table.insertRow(row_position)

    if update_db:
      _id = add({"name": name, "phone_no": phone_no, "email": email, "address": address})

    name_item = QTableWidgetItem(name)
    name_item.setData(Qt.UserRole, _id)

    self.contact_table.setItem(row_position, 0, name_item)
    self.contact_table.setItem(row_position, 1, QTableWidgetItem(phone_no))
    self.contact_table.setItem(row_position, 2, QTableWidgetItem(email))
    self.contact_table.setItem(row_position, 3, QTableWidgetItem(address))

  def search_contact(self):
    query = self.search_input.text().lower()
    found = False

    if not query:
      if self.showing_search_results:
        for rowIdx in range(self.contact_table.rowCount()):
          if self.contact_table.isRowHidden(rowIdx):
            self.contact_table.showRow(rowIdx)

        self.showing_search_results = False
      return

    self.showing_search_results = True

    for row in range(self.contact_table.rowCount()):
      match = False
      for col in range(self.contact_table.columnCount()):
        item = self.contact_table.item(row, col)
        if item and query in item.text().lower():
          match = True
          break

      if not match:
        self.contact_table.hideRow(row)
        found = True

    if not found:
      QMessageBox.information(self, "Not Found", "No contact found matching the query.")
      self.showing_search_results = False

  @display_err_as_critical
  def load_db(self):
    for contact in search():
      self.add_contact(
        name=contact.name,
        phone_no=contact.phone_no,
        address=contact.address,
        email=contact.email,
        _id=contact.id,
      )

  @display_err_as_critical
  def save_changes_to_db(self):
    if self.local_changes:
      for _id, contact in self.local_changes.items():
        update({'id': _id}, contact)

      self.local_changes = {}

    if self.local_deletion_changes:
      for _id in self.local_deletion_changes:
        delete({'id': _id})

      self.local_deletion_changes = set()

    save_changes()


def run():
  app = QApplication(sys.argv)
  window = ContactBook()
  window.show()
  sys.exit(app.exec())
