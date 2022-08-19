from sys import argv
from os import path

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QListView, QComboBox, QTextEdit, QAction, QPushButton, QLabel, \
    QMessageBox


class MainWindow(QMainWindow):

    def __init__(self, add_contact_fun=None, del_contact_fun=None):
        super().__init__()

        self.IMG_DIR = path.join(path.dirname(__file__), 'images').replace('\\', '/')

        self.setFixedSize(740, 530)
        self.setWindowTitle('Мессенджер')
        self.setStyleSheet('font-size: 14px;')

        self.contacts_list = QListView(self)
        self.contacts_list.move(10, 20)
        self.contacts_list.setFixedSize(221, 391)
        self.fill_contacts_list(['Загрузка данных...'])

        self.chat = QListView(self)
        self.chat.move(240, 20)
        self.chat.setFixedSize(491, 391)

        self.add_selector = QComboBox(self)
        self.add_selector.move(10, 420)
        self.add_selector.setFixedSize(175, 31)

        self.add_btn = QPushButton('+', self)
        self.add_btn.move(190, 420)
        self.add_btn.setFixedSize(42, 31)
        self.add_btn.clicked.connect(lambda: self.add_btn_click(add_contact_fun))

        self.del_selector = QComboBox(self)
        self.del_selector.move(10, 460)
        self.del_selector.setFixedSize(175, 31)

        self.del_btn = QPushButton('-', self)
        self.del_btn.move(190, 460)
        self.del_btn.setFixedSize(42, 31)
        self.del_btn.clicked.connect(lambda: self.del_btn_click(del_contact_fun))

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

        self.show()

    def add_btn_click(self, add_contact_fun):
        if self.add_selector.currentIndex() == 0:
            message = QMessageBox()
            message.information(self, ' ', 'Выберите пользователя')
        elif add_contact_fun:
            add_contact_fun(self.add_selector.currentText())

    def del_btn_click(self, del_contact_fun):
        if self.del_selector.currentIndex() == 0:
            message = QMessageBox()
            message.information(self, ' ', 'Выберите пользователя')
        elif del_contact_fun:
            del_contact_fun(self.del_selector.currentText())

    def show_status_message(self, message, error=False):
        self.status_label.setText(message)
        color = '#d21131' if error else '#34973f'
        self.status_label.setStyleSheet(f'font-weight: bold; font-size: 13px; color: {color};')

    def fill_contacts_list(self, clients):
        self.contacts_list.setStyleSheet('background-color: #f6f6f6')
        clients_list = QStandardItemModel(self)
        for client_name in clients:
            item = QStandardItem(client_name)
            item.setEditable(False)
            clients_list.appendRow(item)
        self.contacts_list.setModel(clients_list)

    def fill_add_selector(self, clients):
        self.add_selector.clear()
        self.add_selector.addItem('Добавить контакт')
        self.add_selector.addItems(clients)
        self.add_selector.setCurrentIndex(0)

    def fill_del_selector(self, clients):
        self.del_selector.clear()
        self.del_selector.addItem('Удалить контакт')
        self.del_selector.addItems(clients)
        self.del_selector.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(argv)

    main_window = MainWindow()
    # main_window.show_status_message('Статус подключения')

    main_window.fill_contacts_list(['user2', 'user3'])

    main_window.fill_add_selector(['user1'])

    main_window.fill_del_selector(['user2', 'user3'])

    app.exec_()
