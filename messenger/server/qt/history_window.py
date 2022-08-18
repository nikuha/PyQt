from sys import argv
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QTableView, QHeaderView
from PyQt5.QtCore import Qt


class HistoryWindow(QDialog):
    def __init__(self, get_data=None):
        super().__init__()

        self.setWindowTitle('Статистика клиентов')
        self.setStyleSheet('font-size: 13px;')
        self.setFixedSize(600, 650)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.history_table = QTableView(self)
        self.history_table.move(15, 15)
        self.history_table.setFixedSize(570, 570)

        if get_data:
            def refresh_table():
                self.fill_table(get_data())

            refresh_button = QPushButton('Обновить', self)
            refresh_button.move(230, 600)
            refresh_button.clicked.connect(refresh_table)

            refresh_table()

        close_button = QPushButton('Закрыть', self)
        close_button.move(320, 600)
        close_button.clicked.connect(self.close)

        self.show()

    def fill_table(self, users):
        users_list = QStandardItemModel(self)
        users_list.setHorizontalHeaderLabels([
            'Имя Клиента', 'Последняя авторизация', 'Отправлено', 'Получено'
        ])
        for user in users:
            row = [QStandardItem(user[key]) for key in ['username', 'time', 'sent', 'received']]
            users_list.appendRow(row)
        self.history_table.setModel(users_list)
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # self.history_table.resizeColumnsToContents()


if __name__ == '__main__':
    app = QApplication(argv)

    history_window = HistoryWindow()

    history_window.fill_table([
        {'username': 'test1', 'sent': '10', 'received': '5', 'time': '2022-08-13 15:00'},
        {'username': 'test2', 'sent': '4', 'received': '8', 'time': '2022-08-13 15:12'},
        {'username': 'test3', 'sent': '5', 'received': '12', 'time': '2022-08-13 15:25'},
        {'username': 'test4', 'sent': '8', 'received': '145', 'time': '2022-08-13 16:37'},
    ])

    app.exec_()
