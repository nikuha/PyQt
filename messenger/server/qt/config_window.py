from sys import argv
from PyQt5.QtWidgets import QDialog, QApplication, QLabel, QLineEdit, QPushButton, QFileDialog


class ConfigWindow(QDialog):
    def __init__(self, config_db_path=None, config_db_file=None,
                 config_port=None, config_ip=None, save_function=None):
        super().__init__()

        self.setFixedSize(410, 275)
        self.setWindowTitle('Настройки сервера')
        self.setStyleSheet('font-size: 13px;')

        db_path_label = QLabel('Путь до файла базы данных: ', self)
        db_path_label.move(15, 10)
        db_path_label.setFixedSize(240, 15)

        input_style = 'padding-top: 1px; padding-bottom: 1px; padding-left: 5px; padding-right: 5px;'\
                      'font-size: 12px; border: 1px solid #929292; border-radius: 2px;'

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(270, 25)
        self.db_path.move(15, 34)
        self.db_path.setStyleSheet(input_style)
        self.db_path.setReadOnly(True)
        self.db_path.setText(config_db_path)

        db_path_select = QPushButton('Обзор...', self)
        db_path_select.setFixedSize(100, 26)
        db_path_select.setStyleSheet('border: 1px solid #929292; border-radius: 2px; background-color: #d4d5d6;')
        db_path_select.move(295, 33)

        def open_file_dialog():
            self.dialog = QFileDialog(self)
            path = self.dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.setText(path)

        db_path_select.clicked.connect(open_file_dialog)

        db_file_label = QLabel('Имя файла базы данных: ', self)
        db_file_label.move(15, 79)
        db_file_label.setFixedSize(210, 15)

        self.db_file = QLineEdit(self)
        self.db_file.setStyleSheet(input_style)
        self.db_file.move(230, 75)
        self.db_file.setFixedSize(165, 25)
        self.db_file.setText(config_db_file)

        port_label = QLabel('Номер порта для соединений:', self)
        port_label.move(15, 124)
        port_label.setFixedSize(210, 15)

        self.port = QLineEdit(self)
        self.port.setStyleSheet(input_style)
        self.port.move(230, 120)
        self.port.setFixedSize(165, 25)
        self.port.setText(config_port)

        ip_label = QLabel('С какого IP принимаем соединения:', self)
        ip_label.move(15, 169)
        ip_label.setFixedSize(210, 15)

        self.ip = QLineEdit(self)
        self.ip.setStyleSheet(input_style)
        self.ip.move(230, 165)
        self.ip.setFixedSize(165, 25)
        self.ip.setText(config_ip)

        ip_label_note = QLabel('(оставьте поле пустым, чтобы принимать соединения с любых адресов)', self)
        ip_label_note.setStyleSheet('font-size: 11px;')
        ip_label_note.move(15, 185)
        ip_label_note.setFixedSize(380, 30)

        save_btn = QPushButton('Сохранить', self)
        save_btn.move(230, 230)
        if save_function:
            save_btn.clicked.connect(save_function)

        close_button = QPushButton('Закрыть', self)
        close_button.move(320, 230)
        close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    app = QApplication(argv)
    config_window = ConfigWindow()
    app.exec_()
