from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel , qApp


# Стартовый диалог с выбором имени пользователя
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Вход в мессенджер')
        self.setFixedSize(250, 200)
        self.setStyleSheet('font-size: 14px;')

        label_1 = QLabel('Введите имя пользователя:', self)
        label_1.move(15, 15)
        label_1.setFixedSize(220, 15)

        self.client_name = QLineEdit(self)
        self.client_name.move(15, 40)
        self.client_name.setFixedSize(220, 25)

        label_2 = QLabel('Введите пароль:', self)
        label_2.move(15, 85)
        label_2.setFixedSize(220, 15)

        self.password = QLineEdit(self)
        self.password.move(15, 110)
        self.password.setFixedSize(220, 25)

        self.btn_ok = QPushButton('Вход', self)
        self.btn_ok.move(15, 155)
        self.btn_ok.setFixedSize(105, 25)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.move(130, 155)
        self.btn_cancel.setFixedSize(105, 25)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = LoginDialog()
    app.exec_()
