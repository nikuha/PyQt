from ipaddress import ip_address
from tabulate import tabulate
from task1 import host_ping


def host_range_ping():
    first_ip, diapason = None, None

    while not first_ip:
        first_ip = input('Введите адрес: ')
        try:
            first_ip = ip_address(first_ip)
            break
        except ValueError:
            first_ip = None
            print('Неверный ip-адрес')

    octets = str(first_ip).split('.')
    last_octet = int(octets[3])

    while not diapason:
        try:
            diapason = int(input('Введите количество адресов для проверки: '))
            if diapason < 1 or diapason + last_octet > 256:
                raise ValueError
            break
        except ValueError:
            diapason = None
            print('Неверное количество, допустимый диапазон от 1 до 256')

    ip_list = []
    for i in range(diapason):
        ip_list.append(str(first_ip + i))

    return host_ping(ip_list)


def host_range_ping_tab():
    result_dict = host_range_ping()
    print()
    print(tabulate(result_dict, headers='firstrow'))


if __name__ == '__main__':
    host_range_ping_tab()
