# Импортирует классы из других модулей:
import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.led16_8 import LedShow
from robot.infrared import InfraredControl
import paramiko
import socket
import threading
import os
from logging_config import logger
from robot.actuators import Motor

motor = Motor()

COMMANDS = {
    'forward': (motor.forward, "Робот движется вперёд"),
    'backward': (motor.backward, "Робот движется назад"),
    'left': (motor.left, "Робот поворачивает влево"),
    'right': (motor.right, "Робот поворачивает вправо"),
    'stop': (motor.stop, "Робот остановлен")
}

# Настройки SSH
SSH_HOST = '0.0.0.0' # слушать все интерфейсы
SSH_PORT = 2222
SSH_USERNAME = 'valli'

# Пути к ключам
HOST_KEY_FILE_ED25519 = 'ssh_host_ed25519_key'
HOST_KEY_FILE_RSA = 'ssh_host_rsa_key'  # запасной вариант
AUTHORIZED_KEYS_FILE = '/home/valli/.ssh/authorized_keys'

# Константы
MAX_COMMAND_LENGTH = 100
MAX_CLIENTS = 5
SESSION_TIMEOUT = 300  # 5 минут

# Загружаем авторизованные ключи при старте
def load_authorized_keys():
    try:
        with open(AUTHORIZED_KEYS_FILE, 'r') as f:
            keys = set()
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # игнорируем комментарии
                    keys.add(line)
            return keys
    except FileNotFoundError:
        logger.critical(f"Файл авторизованных ключей не найден: {AUTHORIZED_KEYS_FILE}")
        return set()
    except Exception as e:
        logger.error(f"Ошибка чтения файла ключей: {e}")
        return set()

AUTHORIZED_KEYS = str(load_authorized_keys())  # без str()!

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        if username != SSH_USERNAME:
            logger.warning(f"Неверный пользователь: {username}")
            return paramiko.AUTH_FAILED
        client_key_string = f"{key.get_name()} {key.get_base64()}"
        if client_key_string in AUTHORIZED_KEYS:
            print(f"Успешная аутентификация по ключу для пользователя {username}")
            logger.info(f"Успешная аутентификация по ключу для пользователя {username}")
            return paramiko.AUTH_SUCCESSFUL
        else:
            logger.warning(f"Ключ не авторизован для пользователя {username}: {client_key_string[:50]}...")
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

def handle_command(command):
    command = command.strip().lower()
    if len(command) > MAX_COMMAND_LENGTH:
        return "Ошибка: команда слишком длинная"
    func, response = COMMANDS.get(command, (None, f"Неизвестная команда: {command}"))
    if func:
        try:
            func()
        except Exception as e:
            logger.error(f"Ошибка выполнения команды '{command}': {e}")
            return f"Ошибка выполнения команды: {str(e)}"
    return response

def ssh_session(client):
    logger.info(f"Начало обработки сессии для клиента {client.getpeername()}")

    if client.fileno() == -1:
        logger.warning("Попытка использовать уже закрытый сокет")
        return

    transport = None
    channel = None

    try:
        transport = paramiko.Transport(client)
        transport.banner_timeout = 30
        transport.auth_timeout = 60
        transport.set_keepalive(30)


        # Загружаем ED25519 ключ (предпочтительный)
        if os.path.exists(HOST_KEY_FILE_ED25519):
            host_key = paramiko.Ed25519Key(filename=HOST_KEY_FILE_ED25519)
            print(host_key)
        elif os.path.exists(HOST_KEY_FILE_RSA):

            host_key = paramiko.RSAKey(filename=HOST_KEY_FILE_RSA)
        else:
            logger.info("Генерация ED25519 хост‑ключа...")
            host_key = paramiko.Ed25519Key.generate()
            host_key.write_private_key_file(HOST_KEY_FILE_ED25519)

        transport.add_server_key(host_key)

        server = SSHServer()
        transport.start_server(server=server)

        channel = transport.accept(30)
        if channel is None:
            logger.error("Не удалось открыть канал")
            return

        channel.settimeout(30.0)  # таймаут для чтения

        if not server.event.wait(30):
            logger.error("Shell‑запрос не получен в течение 30 секунд")
            return

        channel.send("Добро пожаловать в управление роботом!\r\n".encode())
        channel.send("Команды: forward, backward, left, right, stop\r\n".encode())

        while True:
            # Очищаем буфер перед отправкой приглашения
            try:
                while channel.recv_ready():
                    channel.recv(1024)
            except Exception as e:
                logger.error(f"Ошибка при очистке буфера: {e}")
                break

            channel.send("$ ".encode())
            try:
                data = channel.recv(1024)
                if not data:  # клиент закрыл соединение
                    print("Клиент закрыл соединение")
                    logger.info("Клиент закрыл соединение")
                    break

                try:
                    command = data.decode('utf-8', errors='replace').strip()
                except UnicodeDecodeError as e:
                    logger.error(f"Ошибка декодирования данных: {e}")
                    channel.send("Ошибка: некорректные данные\r\n".encode())
                    continue  # переходим к следующей итерации цикла

                if command.lower() == 'exit':
                    logger.info("Получен запрос на завершение сессии")
                    break

                response = handle_command(command)
                channel.send((response + "\r\n").encode())

            except socket.timeout:
                logger.warning("Таймаут сессии — нет активности в течение 30 секунд")
                break
            except Exception as e:
                logger.error(f"Критическая ошибка в SSH‑сессии: {e}")
                break

    except KeyboardInterrupt:
        logger.info("Сессия прервана пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в SSH‑сессии: {e}")
    finally:
        # Корректное закрытие ресурсов
        try:
            if channel and channel.active:
                channel.close()
                logger.debug("Канал закрыт")
        except Exception as e:
            logger.error(f"Ошибка при закрытии канала: {e}")

        try:
            if transport and transport.is_active():
                transport.close()
                logger.debug("Транспорт закрыт")
        except Exception as e:
            logger.error(f"Ошибка при закрытии транспорта: {e}")

        try:
            if client and hasattr(client, 'fileno') and client.fileno() != -1:
                client.close()
                logger.debug("Сокет клиента закрыт")
        except OSError as e:
            if e.errno != 9:
                logger.error(f"Ошибка при закрытии сокета: {e}")



def start_ssh_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((SSH_HOST, SSH_PORT))
        sock.listen(MAX_CLIENTS)
        sock.settimeout(1.0)  # Таймаут для accept()
        logger.info(f"SSH‑сервер запущен на порту {SSH_PORT} с аутентификацией по ключу")
    except OSError as e:
        logger.critical(f"Не удалось запустить сервер: {e}")
        return

    active_threads = []

    try:
        while True:
            active_threads = cleanup_threads(active_threads)  # Очистка перед новым подключением
            print(active_threads)
            try:
                logger.debug(f"Состояние сокета перед accept(): fileno={sock.fileno()}, closed={sock._closed}")
                client, addr = sock.accept()
                logger.debug(f"Новый клиент принят: {addr}, fileno={client.fileno()}")
                logger.info(f"Новое подключение от {addr}")

                # Очистка списка активных потоков
                active_threads[:] = [t for t in active_threads if t.is_alive()]
                
                # Ограничение числа активных подключений
                if len(active_threads) >= MAX_CLIENTS:
                    logger.warning(f"Достигнут лимит подключений. Отказано клиенту {addr}")
                    client.close()
                    continue

                thread = threading.Thread(target=ssh_session, args=(client,))
                thread.daemon = True
                thread.start()
                active_threads.append(thread)

            except socket.timeout:
                continue  # Возвращаемся к началу цикла
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки. Завершение работы...")
    except OSError as e:
        if e.errno == 9:
            logger.critical("Критическая ошибка: серверный сокет закрыт (Errno 9). Остановка сервера.")
    # except Exception as e:
    #     logger.critical(f"Критическая ошибка сервера: {e}")
    finally:
        # Закрываем серверный сокет только здесь
        try:
            sock.close()
        except:
            pass
        logger.info("Сервер остановлен.")



def cleanup_threads(active_threads_list):
    """Удаляет из списка завершённые потоки и закрывает их сокеты"""
    to_remove = []
    for thread in active_threads_list:
        if not thread.is_alive():
            to_remove.append(thread)
    for thread in to_remove:
        active_threads_list.remove(thread)
    return active_threads_list


if __name__ == "__main__":
    logger.info("Запуск SSH‑сервера...")
    logger.info(f"Авторизованные ключи загружены: {len(AUTHORIZED_KEYS)}")
    start_ssh_server()


# # бегущая строка

# led16_8 = LedShow
# try:
#     led16_8.scroll_text("Привет", delay=0.15)

# except KeyboardInterrupt:
#     print("Прервано пользователем")

# finally:
#     # Гарантированная очистка
#     led16_8.matrix_display([0x00] * 16)  # Очистить матрицу
#     GPIO.cleanup()
#     print("Завершено")







