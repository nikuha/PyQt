import os
from sys import argv
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp, QLabel, QTableView, QHeaderView


class MainWindow(QMainWindow):

    def __init__(self, show_history_window=None, show_config_window=None):
        super().__init__()

        self.IMG_DIR = os.path.join(os.path.dirname(__file__), 'images')

        self.setFixedSize(800, 600)
        self.setWindowTitle('Сервер чата')
        self.setStyleSheet('font-size: 14px;')

        toolbar = self.addToolBar('MainBar')
        toolbar.setStyleSheet("height: 30px;")

        show_history_button = QAction('Статистика клиентов', self)
        toolbar.addAction(show_history_button)
        if show_history_window:
            show_history_button.triggered.connect(show_history_window)

        config_btn = QAction('Настройки сервера', self)
        toolbar.addAction(config_btn)
        if show_config_window:
            config_btn.triggered.connect(show_config_window)

        exit_btn = QAction(QIcon(f'{self.IMG_DIR}/exit.png'), 'Выход', self)
        exit_btn.setShortcut('Ctrl+Q')
        exit_btn.triggered.connect(qApp.quit)
        toolbar.addAction(exit_btn)

        label = QLabel('Список подключённых клиентов:', self)
        label.setFixedSize(400, 30)
        label.move(18, 50)

        self.connections_table = QTableView(self)
        self.connections_table.move(18, 90)
        self.connections_table.setFixedSize(764, 470)
        self.connections_table.setStyleSheet('font-size: 13px;')

        self.show()

    def show_status_message(self, message, error=False):
        color = '#d21131' if error else '#34973f'
        self.statusBar().setStyleSheet(f'font-weight: bold; font-size: 14px; color: {color};')
        self.statusBar().showMessage(f'   {message}')

    def fill_table(self, clients):
        clients_list = QStandardItemModel(self)
        clients_list.setHorizontalHeaderLabels(['Имя Клиента', 'Время подключения', 'IP Адрес', 'Порт'])
        for client in clients:
            row = [QStandardItem(client[key]) for key in ['username', 'time', 'ip', 'port']]
            clients_list.appendRow(row)
        self.connections_table.setModel(clients_list)
        header = self.connections_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        # self.connections_table.resizeColumnsToContents()


if __name__ == '__main__':
    app = QApplication(argv)

    main_window = MainWindow()

    main_window.show_status_message('Success Statusbar Message')
    # main_window.show_status_message('Error Message', True)

    main_window.fill_table([
        {'username': 'test1', 'ip': '192.168.1.10', 'port': '1234', 'time': '2022-08-13 15:00'},
        {'username': 'test2', 'ip': '192.168.1.4', 'port': '7234', 'time': '2022-08-13 15:12'},
        {'username': 'test3', 'ip': '192.168.1.5', 'port': '7234', 'time': '2022-08-13 15:25'},
        {'username': 'test4', 'ip': '192.168.1.8', 'port': '7234', 'time': '2022-08-13 16:37'},
    ])

    app.exec_()
