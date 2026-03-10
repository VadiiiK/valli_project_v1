# Импортирует классы из других модулей:
# import time
# from robot.gpio_manager import GPIOManager
# from robot.led16_8 import LedShow
# from robot.infrared import InfraredControl
import paramiko
import socket
import threading
import os
import logging
from logging_config import logger
from robot.actuators import Motor

# Настройки SSH
SSH_HOST = '0.0.0.0'
SSH_PORT = 2222
SSH_USERNAME = 'valli'

# Пути к ключам
HOST_KEY_FILE_ED25519 = 'ssh_host_ed25519_key'
HOST_KEY_FILE_RSA = 'ssh_host_rsa_key'  # запасной вариант
AUTHORIZED_KEYS_FILE = 'authorized_keys'

# Константы
MAX_COMMAND_LENGTH = 100
MAX_CLIENTS = 50
SESSION_TIMEOUT = 300  # 5 минут

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        """Проверка публичного ключа клиента"""
        if username != SSH_USERNAME:
            logger.warning(f"Неверный пользователь: {username}")
            return paramiko.AUTH_FAILED

        # Загружаем авторизованные ключи
        try:
            with open(AUTHORIZED_KEYS_FILE, 'r') as f:
                authorized_keys = f.read().strip().split('\n')
        except FileNotFoundError:
            logger.critical(f"Файл авторизованных ключей не найден: {AUTHORIZED_KEYS_FILE}")
            return paramiko.AUTH_FAILED
        except Exception as e:
            logger.error(f"Ошибка чтения файла ключей: {e}")
            return paramiko.AUTH_FAILED

        # Конвертируем ключ клиента в строку для сравнения
        client_key_string = f"{key.get_name()} {key.get_base64()}"

        if client_key_string in authorized_keys:
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
    """Обрабатывает команды управления роботом с обработкой ошибок"""
    logger.debug(f"Получена команда: {command}")
    command = command.strip().lower()

    # Валидация длины команды
    if len(command) > MAX_COMMAND_LENGTH:
        logger.warning("Команда превышает максимальную длину")
        return "Ошибка: команда слишком длинная"

    try:
        if command == 'forward':
            Motor.forward()
            response = "Робот движется вперёд"
        elif command == 'backward':
            Motor.backward()
            response = "Робот движется назад"
        elif command == 'left':
            Motor.left()
            response = "Робот поворачивает влево"
        elif command == 'right':
            Motor.right()
            response = "Робот поворачивает вправо"
        elif command == 'stop':
            Motor.stop()
            response = "Робот остановлен"
        else:
            response = f"Неизвестная команда: {command}"
            logger.warning(response)
    except Exception as e:
        logger.error(f"Ошибка выполнения команды '{command}': {e}")
        response = f"Ошибка выполнения команды: {str(e)}"

    logger.info(f"Команда '{command}' выполнена. Ответ: {response}")
    return response

def ssh_session(client):
    try:
        transport = paramiko.Transport(client)
        transport.set_keepalive(30)  # Отправка keepalive каждые 30 секунд

        # Загружаем или генерируем хост‑ключи
        host_keys = []

        # Ed25519 — основной ключ
        if not os.path.exists(HOST_KEY_FILE_ED25519):
            logger.info("Генерация нового Ed25519 хост‑ключа...")
            host_key_ed25519 = paramiko.Ed25519Key.generate()
            host_key_ed25519.write_private_key_file(HOST_KEY_FILE_ED25519)
        else:
            host_key_ed25519 = paramiko.Ed25519Key(filename=HOST_KEY_FILE_ED25519)
        host_keys.append(host_key_ed25519)

        # RSA — запасной вариант для старых клиентов
        if not os.path.exists(HOST_KEY_FILE_RSA):
            logger.info("Генерация резервного RSA хост‑ключа...")
            host_key_rsa = paramiko.RSAKey.generate(2048)
            host_key_rsa.write_private_key_file(HOST_KEY_FILE_RSA)
        else:
            host_key_rsa = paramiko.RSAKey(filename=HOST_KEY_FILE_RSA)
        host_keys.append(host_key_rsa)

        for key in host_keys:
            transport.add_server_key(key)

        server = SSHServer()
        transport.start_server(server=server)

        channel = transport.accept(20)
        if channel is None:
            logger.error("Не удалось открыть канал")
            return

        # Ожидание shell‑запроса с таймаутом
        if not server.event.wait(10):
            logger.error("Shell‑запрос не получен в течение 10 секунд")
            return

        channel.send("Добро пожаловать в управление роботом!\r\n")
        channel.send("Команды: forward, backward, left, right, stop\r\n")

        while True:
            channel.send("$ ")
            # Таймаут для чтения данных
            data = channel.recv(1024)
            if not data:
                break

            # Декодирование с обработкой ошибок
            try:
                command = data.decode('utf-8', errors='replace').strip()
            except UnicodeDecodeError as e:
                logger.error(f"Ошибка декодирования данных: {e}")
                channel.send("Ошибка: некорректные данные\r\n")
                continue

            if command.lower() == 'exit':
                break

            response = handle_command(command)
            channel.send(response + "\r\n")

    except socket.timeout:
        logger.warning("Таймаут сессии")
    except Exception as e:
        logger.error(f"Критическая ошибка в SSH‑сессии: {e}")
    finally:
        try:
            client.close()
        except:
            pass

def start_ssh_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Linux

    try:
        sock.bind((SSH_HOST, SSH_PORT))
        sock.listen(MAX_CLIENTS)
        logger.info(f"SSH‑сервер запущен на порту {SSH_PORT} с аутентификацией по ключу")
    except OSError as e:
        logger.critical(f"Не удалось запустить сервер: {e}")
        return

    active_threads = []

    try:
        while True:
            client, addr = sock.accept()
            logger.info(f"Новое подключение от {addr}")

            # Ограничение числа активных подключений
            if len(active_threads) >= MAX_CLIENTS:
                logger.warning(f"Достигнут лимит подключений. Отказано клиенту {addr}")
                client.close()
                continue

            thread = threading.Thread(target=ssh_session, args=(client,))
            thread.daemon = True
            thread.start()
            active_threads.append(thread)

            # Очистка завершённых потоков
            active_threads = [t for t in active_threads if t.is_alive()]

    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки. Завершение работы...")
    except Exception as e:
        logger.critical(f"Критическая ошибка сервера: {e}")
    finally:
        sock.close()
        logger.info("Сервер остановлен.")

if __name__ == "__main__":
    start_ssh_server()


# бегущая строка
# try:
#     led16_8.scroll_text("Привет", delay=0.15)

# except KeyboardInterrupt:
#     print("Прервано пользователем")

# finally:
#     # Гарантированная очистка
#     led16_8.matrix_display([0x00] * 16)  # Очистить матрицу
#     gpio.cleanup()
#     print("Завершено")


# Подключение датчика расстояния
# sensor = DistanceSensor(gpio)


# Подключение моторов
# left_motor = Motor(gpio, pin=12)
# right_motor = Motor(gpio, pin=13)


# Подключение сервопривода
# servo = Servo(gpio)


# Логика движения
# navigator = Navigator(sensor, left_motor, right_motor)


# Запускает главный цикл (меню управления):
# while True:
#     show_menu()  # выводит список команд
#     cmd = input("> ").strip().lower()


#     if cmd == 'f':
#         navigator.move_forward(50)  # ехать вперёд
#     elif cmd.startswith('s'):
#         angle = int(cmd[1:])
#         servo.set_angle(angle)     # повернуть серву
#     elif cmd == 'd':
#         print(f"Расстояние: {sensor.get_distance()} см")
#     elif cmd == 'a':
#         navigator.avoid_obstacle()  # авторежим
#     elif cmd == 'q':
#         break  # выход


# # Очищает ресурсы при завершении:
# gpio.cleanup()  # отключает все пины GPIO



