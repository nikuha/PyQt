from sys import argv

from PyQt5.QtWidgets import QDialog, QApplication, QComboBox, QPushButton, QLineEdit, QLabel, QMessageBox
from PyQt5.QtCore import Qt


class UsersWindow(QDialog):
    def __init__(self, add_user_fun=None, del_user_fun=None, get_del_users_list_fun=None):
        super().__init__()

        self.setWindowTitle('Управление пользователями')
        self.setStyleSheet('font-size: 13px;')
        self.setFixedSize(425, 140)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.del_selector = QComboBox(self)
        self.del_selector.move(10, 20)
        self.del_selector.setFixedSize(300, 30)

        self.del_btn = QPushButton('Удалить', self)
        self.del_btn.move(315, 20)
        self.del_btn.setFixedSize(100, 30)

        username_label = QLabel('Имя пользователя: ', self)
        username_label.move(10, 70)
        username_label.setFixedSize(145, 15)

        password_label = QLabel('Пароль: ', self)
        password_label.move(165, 70)
        password_label.setFixedSize(145, 15)

        input_style = 'padding-top: 1px; padding-bottom: 1px; padding-left: 5px; padding-right: 5px;'\
                      'font-size: 12px; border: 1px solid #929292; border-radius: 2px;'

        self.username = QLineEdit(self)
        self.username.setStyleSheet(input_style)
        self.username.move(10, 90)
        self.username.setFixedSize(145, 30)

        self.password = QLineEdit(self)
        self.password.setStyleSheet(input_style)
        self.password.move(165, 90)
        self.password.setFixedSize(145, 30)

        self.add_btn = QPushButton('Добавить', self)
        self.add_btn.move(315, 90)
        self.add_btn.setFixedSize(100, 30)

        # self.close_btn = QPushButton('Закрыть', self)
        # self.close_btn.move(315, 225)
        # self.close_btn.setFixedSize(100, 30)
        # self.close_btn.clicked.connect(lambda: self.close())

        self.message = QMessageBox()

        self.del_selector.currentIndexChanged.connect(self._del_selector_changed)
        self.add_btn.clicked.connect(lambda: self._add_user(add_user_fun))
        self.del_btn.clicked.connect(lambda: self._del_user(del_user_fun))

        self.get_del_users_list_fun = get_del_users_list_fun
        self.fill_del_selector()

        self.show()

    def fill_del_selector(self, users=None):
        if self.get_del_users_list_fun:
            users = self.get_del_users_list_fun()
        elif not users:
            return
        self.del_selector.clear()
        self.del_selector.addItem('Удалить пользователя')
        self.del_selector.addItems(users)
        self.del_selector.setCurrentIndex(0)

    def _del_selector_changed(self):
        if self.del_selector.currentIndex() == 0 or self.del_selector.count() < 2:
            self.del_btn.setDisabled(True)
        else:
            self.del_btn.setDisabled(False)

    def _del_user(self, del_user_fun):
        if not del_user_fun:
            return
        if not self.del_selector.currentIndex():
            self.message.information(self, 'Подсказка', 'Выберите пользователя!')
            return
        if del_user_fun(self.del_selector.currentText()):
            self.message.information(self, 'OK', 'Пользователь удален!')
        self.fill_del_selector()

    def _add_user(self, add_user_fun):
        if not add_user_fun:
            return
        username = self.username.text()
        password = self.password.text()
        if not username:
            self.message.information(self, 'Ошибка', 'Не указано имя пользователя.')
            return
        if not password:
            self.message.information(self, 'Ошибка', 'Не указан пароль.')
            return
        result = add_user_fun(username, password)
        if not (result is True):
            self.message.information(self, 'Ошибка', result)
            return
        self.message.information(self, 'OK', 'Пользователь добавлен!')
        self.fill_del_selector()
        self.username.clear()
        self.password.clear()


if __name__ == '__main__':
    app = QApplication(argv)

    users_window = UsersWindow()
    users_window.fill_del_selector(['test1', 'test2'])

    app.exec_()
