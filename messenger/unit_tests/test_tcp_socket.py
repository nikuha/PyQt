import os
import sys
import json
from unittest import mock, TestCase, main as unittest_main
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.tcp_socket import TCPSocket
import common.settings as settings


class TestTCPSocket(TestCase):
    def setUp(self):
        self.mock_socket = mock.Mock()
        self.some_dict = {'message': 'Любой словарь для отправки или получения'}
        self.some_string = 'Неверное сообщение в виде строки'

    def mock_byte_response(self, dict_response: dict):
        """Имитируем получение байтовых данных"""
        json_data = json.dumps(dict_response)
        self.mock_socket.recv.return_value = json_data.encode(settings.ENCODING)

    def test_get_message(self):
        """Получение сообщения"""
        self.mock_byte_response(self.some_dict)
        result = TCPSocket.get_message(self.mock_socket)
        self.assertEqual(result, self.some_dict)

    def test_get_message_error(self):
        """Получение неверного сообщения"""
        self.mock_socket.recv.return_value = self.some_string
        with self.assertRaises(ValueError):
            TCPSocket.get_message(self.mock_socket)

    def test_send_message(self):
        """Отправка верного сообщения"""
        result = TCPSocket.send_message(self.mock_socket, self.some_dict)
        self.assertTrue(result)

    def test_send_message_error(self):
        """Отправка неверного сообщения"""
        with self.assertRaises(ValueError):
            TCPSocket.send_message(self.mock_socket, self.some_string)

    def test_int_port(self):
        """Преобразование порта в int"""
        result = TCPSocket.int_port('2222')
        self.assertEqual(result, 2222)

    def test_int_port_error(self):
        """Возвращение пустого значения"""
        result = TCPSocket.int_port('1000')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest_main()
