import os
import sys
from unittest import mock, TestCase, main as unittest_main
import time
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import MsgServer
import common.settings as settings


class TestServer(TestCase):
    def setUp(self):
        with mock.patch('socket.socket') as _:
            self.server = MsgServer()

    def test_process_message_correct(self):
        """Верный запрос присутствия к серверу"""
        message = {
            settings.REQUEST_ACTION: settings.ACTION_PRESENCE,
            settings.REQUEST_TIME: time.time(),
            settings.REQUEST_USER: {settings.REQUEST_ACCOUNT_NAME: 'Guest'}
        }
        result = self.server._process_message(message)
        self.assertEqual(result, {'status': 200, 'message': 'Вы онлайн'})

    def test_process_message_no_action(self):
        """Запрос не содержит action"""
        message = {
            settings.REQUEST_TIME: time.time(),
            settings.REQUEST_USER: {settings.REQUEST_ACCOUNT_NAME: 'Guest'}
        }
        result = self.server._process_message(message)
        self.assertEqual(result, {'status': 400, 'error': 'Неверный запрос!'})

    def test_process_message_wrong_action(self):
        """Неверный action"""
        message = {
            settings.REQUEST_ACTION: 'something',
            settings.REQUEST_TIME: time.time(),
            settings.REQUEST_USER: {settings.REQUEST_ACCOUNT_NAME: 'Guest'}
        }
        result = self.server._process_message(message)
        self.assertEqual(result, {'status': 400, 'error': 'Неверный параметр action!'})

    def test_process_message_wrong_user(self):
        """Неверный пользователь"""
        message = {
            settings.REQUEST_ACTION: settings.ACTION_PRESENCE,
            settings.REQUEST_TIME: time.time()
        }
        result = self.server._process_message(message)
        self.assertEqual(result, {'status': 400, 'error': 'Неверный запрос присутствия!'})


if __name__ == '__main__':
    unittest_main()
