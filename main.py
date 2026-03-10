# Импортирует классы из других модулей:
# import time
import paramiko
import socket
import threading
import RPi.GPIO as GPIO
from logging_config import logger
# from robot.gpio_manager import GPIOManager
# from robot.led16_8 import LedShow
# from robot.infrared import InfraredControl
from robot.actuators import Motor


# Настройки SSH
SSH_HOST = '0.0.0.0'
SSH_PORT = 2222
SSH_USERNAME = 'valli'
SSH_PASSWORD = 'valli'

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == SSH_USERNAME and password == SSH_PASSWORD:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
def handle_command(command):
    print(command)
    command = command.strip().lower()
    if command == 'forward':
        Motor.forward()
        return "Робот движется вперёд"
    elif command == 'backward':
        Motor.backward()
        return "Робот движется назад"
    elif command == 'left':
        Motor.left()
        return "Робот поворачивает влево"
    elif command == 'right':
        Motor.right()
        return "Робот поворачивает вправо"
    elif command == 'stop':
        Motor.stop()
        return "Робот остановлен"
    else:
        return f"Неизвестная команда: {command}"
    

def ssh_session(client):
    try:
        transport = paramiko.Transport(client)
        host_key = paramiko.RSAKey.generate(2048)
        transport.add_server_key(host_key)
        server = SSHServer()
        transport.start_server(server=server)

        channel = transport.accept(20)
        if channel is None:
            print("Не удалось открыть канал")
            return

        # Ожидание shell‑запроса
        server.event.wait(10)
        if not server.event.is_set():
            print("Shell‑запрос не получен")
            return

        channel.send("Добро пожаловать в управление роботом!\r\n")
        channel.send("Команды: forward, backward, left, right, stop\r\n")

        while True:
            channel.send("$ ")
            data = channel.recv(1024)
            if not data:
                break
            command = data.decode('utf-8').strip()
            if command.lower() == 'exit':
                break
            response = handle_command(command)
            channel.send(response + "\r\n")
    except Exception as e:
        print(f"Ошибка в SSH‑сессии: {e}")
    finally:
        client.close()

def start_ssh_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((SSH_HOST, SSH_PORT))
    sock.listen(100)
    print(f"SSH‑сервер запущен на порту {SSH_PORT}")

    try:
        while True:
            client, addr = sock.accept()
            print(f"Подключение от {addr}")
            thread = threading.Thread(target=ssh_session, args=(client,))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
    finally:
        sock.close()
        GPIO.cleanup()


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



