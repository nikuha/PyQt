import time
from sys import argv
from os import path

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSlot, QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QListView, QComboBox, QTextEdit, QPushButton, QLabel, QMessageBox


class MainWindow(QMainWindow):

    def __init__(self, add_contact_fun=None, del_contact_fun=None, user_chat_fun=None, send_message_fun=None):
        super().__init__()

        self.IMG_DIR = path.join(path.dirname(__file__), 'images').replace('\\', '/')
        self.add_contact_fun = add_contact_fun

        self.setFixedSize(740, 530)
        self.setWindowTitle('Мессенджер')
        self.setStyleSheet('font-size: 14px;')

        self.contacts_list = QListView(self)
        self.contacts_list.move(10, 20)
        self.contacts_list.setFixedSize(221, 391)
        self.contacts_list.setStyleSheet('background-color: #f6f6f6')

        self.chat = QListView(self)
        self.chat.move(240, 20)
        self.chat.setFixedSize(491, 391)
        self.chat.setStyleSheet('background-color: #f6f6f6')

        self.add_selector = QComboBox(self)
        self.add_selector.move(10, 420)
        self.add_selector.setFixedSize(175, 31)

        self.add_btn = QPushButton('+', self)
        self.add_btn.move(190, 420)
        self.add_btn.setFixedSize(42, 31)

        self.del_selector = QComboBox(self)
        self.del_selector.move(10, 460)
        self.del_selector.setFixedSize(175, 31)

        self.del_btn = QPushButton('-', self)
        self.del_btn.move(190, 460)
        self.del_btn.setFixedSize(42, 31)

        self.message_field = QTextEdit(self)
        self.message_field.move(240, 420)
        self.message_field.setFixedSize(431, 71)

        self.message_btn = QPushButton(self)
        self.message_btn.move(671, 421)
        self.message_btn.setFixedSize(61, 71)
        self.message_btn.setStyleSheet(f"border: none; background-image : url({self.IMG_DIR}/send.png);")

        self.status_label = QLabel('Соединение...', self)
        self.status_label.move(15, 500)
        self.status_label.setFixedSize(700, 15)
        self.setStyleSheet('font-size: 13px;')

        self.messages = QMessageBox()

        self.add_btn.setDisabled(True)
        self.del_btn.setDisabled(True)
        self.message_field.setDisabled(True)
        self.message_btn.setDisabled(True)

        self.loaded_chat = None

        self._fill_contacts_list(['Загрузка данных...'])
        self.contacts_list.doubleClicked.connect(lambda: self._load_user_chat(user_chat_fun))

        self.add_selector.currentIndexChanged.connect(self._add_selector_changed)
        self.add_btn.clicked.connect(lambda: self._add_btn_click(add_contact_fun))

        self.del_selector.currentIndexChanged.connect(self._del_selector_changed)
        self.del_btn.clicked.connect(lambda: self._del_btn_click(del_contact_fun))

        self.message_btn.clicked.connect(lambda: self._message_btn_click(send_message_fun))

        self.show()

    def make_connection(self, signals):
        signals['lost_connection_signal'].connect(self._lost_connection_slot)
        signals['load_data_signal'].connect(self._load_data_slot)
        signals['fill_chat_signal'].connect(self._fill_chat_slot)
        signals['status_message_signal'].connect(self._status_message_slot)
        signals['unlock_message_components_signal'].connect(self._unlock_message_components_slot)

    def _load_user_chat(self, user_chat_fun):
        if user_chat_fun:
            user_chat_fun(self.contacts_list.currentIndex().data(), True)

    def _add_selector_changed(self):
        if self.add_selector.currentIndex() == 0 or self.add_selector.count() < 2:
            self.add_btn.setDisabled(True)
        else:
            self.add_btn.setDisabled(False)

    def _del_selector_changed(self):
        if self.del_selector.currentIndex() == 0 or self.del_selector.count() < 2:
            self.del_btn.setDisabled(True)
        else:
            self.del_btn.setDisabled(False)

    def _add_btn_click(self, add_contact_fun):
        self.add_btn.setDisabled(True)
        self._show_status_message('Добавление контакта...')
        if add_contact_fun:
            add_contact_fun(self.add_selector.currentText())

    def _del_btn_click(self, del_contact_fun):
        self.del_btn.setDisabled(True)
        self._show_status_message('Удаление контакта...')
        if del_contact_fun:
            del_contact_fun(self.del_selector.currentText())

    def _lock_message_components(self):
        self.message_btn.setDisabled(True)
        self.message_field.setDisabled(True)

    def _clear_message_field(self):
        self.message_field.clear()

    def _message_btn_click(self, send_message_fun):
        self._lock_message_components()
        self._show_status_message('Отправка сообщения...')
        if send_message_fun:
            send_message_fun(self.contacts_list.currentIndex().data(), self.message_field.toPlainText())

    def _unlock_message_components(self):
        self.message_btn.setDisabled(False)
        self.message_field.setDisabled(False)

    def _show_status_message(self, message, error=False):
        self.status_label.setText(message)
        color = '#d21131' if error else '#34973f'
        self.status_label.setStyleSheet(f'font-size: 13px; color: {color};')

    def _fill_contacts_list(self, clients):
        clients_list = QStandardItemModel(self)
        for client_name in clients:
            item = QStandardItem(client_name)
            item.setEditable(False)
            clients_list.appendRow(item)
        self.contacts_list.setModel(clients_list)
        if self.loaded_chat:
            if contact_item := self._get_contact_item(self.loaded_chat):
                self._select_contact_item(contact_item)
            self.loaded_chat = None
            self._unlock_message_components()
        else:
            self._clear_chat()
            self._lock_message_components()

    def _fill_add_selector(self, clients):
        self.add_selector.clear()
        self.add_selector.addItem('Добавить контакт')
        self.add_selector.addItems(clients)
        self.add_selector.setCurrentIndex(0)

    def _fill_del_selector(self, clients):
        self.del_selector.clear()
        self.del_selector.addItem('Удалить контакт')
        self.del_selector.addItems(clients)
        self.del_selector.setCurrentIndex(0)

    def _fill_chat(self, messages):
        messages_list = QStandardItemModel(self)
        for message in messages:
            item = QStandardItem(message['text'])
            item.setEditable(False)
            if message['position'] == 'right':
                item.setTextAlignment(Qt.AlignRight)
                item.setBackground(QBrush(QColor(217, 221, 237)))
            else:
                item.setBackground(QBrush(QColor(237, 234, 217)))
            messages_list.appendRow(item)
        self.chat.setModel(messages_list)
        self.chat.scrollToBottom()

    def _clear_chat(self):
        self._fill_chat([])

    def _show_alert(self, title, text):
        self.messages.information(self, title, text)

    def _get_contact_item(self, text):
        model = self.contacts_list.model()
        match = model.match(
            model.index(0, self.contacts_list.modelColumn()),
            Qt.DisplayRole,
            text,
            hits=1,
            flags=Qt.MatchStartsWith)
        if match:
            return match[0]
        return None

    def _select_contact_item(self, contact_item):
        self.contacts_list.setCurrentIndex(contact_item)
        self._unlock_message_components()

    @pyqtSlot(dict)
    def _lost_connection_slot(self, data):
        title = data['title'] if 'title' in data else 'Сбой соединения'
        message = data['message'] if 'title' in data else 'Потеряно соединение с сервером. '
        self.messages.critical(self, title, message)
        self.close()

    @pyqtSlot(list, list)
    def _load_data_slot(self, contacts, users):
        if (not contacts) or (contacts and contacts[0]):
            self._fill_contacts_list(contacts)
            self._fill_del_selector(contacts)
        self._fill_add_selector(users)

    @pyqtSlot(str, list, bool)
    def _fill_chat_slot(self, username, messages, clear_field):
        show_flag = True
        if self.contacts_list.currentIndex().data() != username:
            if contact_item := self._get_contact_item(username):
                show_flag = self.messages.question(
                    self,
                    'Новое сообщение',
                    f'Пришло новое сообщение от {username}\nОткрыть чат?',
                    QMessageBox.Yes,
                    QMessageBox.No) == QMessageBox.Yes
                if show_flag:
                    self._select_contact_item(contact_item)
            else:
                show_flag = self.messages.question(
                    self,
                    'Новое сообщение',
                    f'Пришло новое сообщение от {username} не из списка контактов\n'
                    'Добавить в контакты и открыть чат с ним?',
                    QMessageBox.Yes,
                    QMessageBox.No) == QMessageBox.Yes
                self.loaded_chat = username
                if show_flag:
                    self.add_contact_fun(username)
        if show_flag:
            self._fill_chat(messages)
            if not self.loaded_chat:
                self._unlock_message_components()
                if clear_field:
                    self._clear_message_field()

    @pyqtSlot()
    def _unlock_message_components_slot(self):
        self._unlock_message_components()

    @pyqtSlot(str, bool)
    def _status_message_slot(self, message, error):
        self._show_status_message(message, error)


if __name__ == '__main__':
    app = QApplication(argv)

    main_window = MainWindow()
    main_window._show_status_message('Статус подключения')

    main_window._fill_contacts_list(['user2', 'user3'])

    main_window._fill_add_selector(['user1'])

    main_window._fill_del_selector(['user2', 'user3'])

    # print(main_window.select_contact('user4'))

    app.exec_()
