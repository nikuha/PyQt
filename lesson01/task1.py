import platform
from subprocess import Popen, PIPE
from tabulate import tabulate
import threading


def host_ping(ip_list):
    true_results = []
    false_results = []
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    def ping(current_ip):
        process = Popen(['ping', param, '5', current_ip], stdout=PIPE, stderr=PIPE)
        if process.wait() == 0:
            true_results.append(current_ip)
        else:
            false_results.append(current_ip)

    for ip in ip_list:
        worker = threading.Thread(target=ping, args=(ip,))
        worker.daemon = True
        worker.start()

    while True:
        true_results_len, false_results_len = len(true_results),  len(false_results)
        if true_results_len + false_results_len < len(ip_list):
            continue

        true_results.sort()
        false_results.sort()

        results = [{'1': 'Доступные узлы', '0': 'Недоступные узлы'}]

        for i in range(max(true_results_len, false_results_len)):
            true_value = true_results[i] if i < true_results_len else ''
            false_value = false_results[i] if i < false_results_len else ''
            results.append({'1': true_value, '0': false_value})

        return results


if __name__ == '__main__':
    print(tabulate(host_ping(['8.8.8.8', 'a', 'yandex.ru']), headers='firstrow'))
