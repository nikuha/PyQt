import os
import sys
from unittest import mock, TestCase, main as unittest_main
sys.path.append(os.path.join(os.getcwd(), '..'))
from client import MsgClient
import common.settings as settings
import json


class TestClient(TestCase):
    def setUp(self):
        with mock.patch('socket.socket') as mock_socket:
            self.mock_socket = mock_socket
            self.client = MsgClient()

    def mock_byte_response(self, dict_response: dict):
        """Имитируем получение байтовых данных"""
        json_data = json.dumps(dict_response)
        self.mock_socket.return_value.recv.return_value = json_data.encode(settings.ENCODING)

    def test_get_response_200(self):
        """Обработка верного ответа присутствия"""
        self.mock_byte_response({
            'status': 200,
            'message': 'Вы онлайн'
        })
        result = self.client._get_response()
        self.assertEqual(result, 'Status: 200, Вы онлайн')

    def test_get_response_wrong(self):
        """Обработка некорректного ответа сервера"""
        self.mock_byte_response({
            'message': 'Вы онлайн'
        })
        result = self.client._get_response()
        self.assertEqual(result, 'Неизвестный ответ сервера!')

    def test_get_response_400(self):
        """Обработка ответа сервера с ошибкой"""
        self.mock_byte_response({
            'status': 400,
            'error': 'Неверный запрос присутствия!'
        })
        result = self.client._get_response()
        self.assertEqual(result, 'Status: 400, Неверный запрос присутствия!')


if __name__ == '__main__':
    unittest_main()
