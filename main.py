# Импортирует классы из других модулей:
from logging_config import logger
from robot.gpio_manager import GPIOManager
from robot.led16_8 import LedShow
from robot.infrared import InfraredControl
import time
# from robot.sensors import DistanceSensor
# from robot.actuators import Motor, Servo
# from robot.navigation import Navigator
# from utils.cli import show_menu




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
# import evdev
# from evdev import ecodes

# device = evdev.InputDevice('/dev/input/event3')  # замените на ваш eventX


# for event in device.read_loop():
#     if event.type == ecodes.EV_KEY:
#         key_event = evdev.categorize(event)
#         if key_event.keystate == key_event.key_down:
#             print(f"Нажата: {key_event.keycode}")

import evdev
import time

# def find_keyboard():
#     print(evdev.list_devices())
#     for path in evdev.list_devices():
#         device = evdev.InputDevice(path)
#         if 'Mouse' in device.name.lower():
#             return device
#     raise IOError("Клавиатура не найдена!")

# device = find_keyboard()
device = evdev.InputDevice('/dev/input/event6')

try:
    print(f"Мониторинг {device.name}. Нажмите Ctrl+C для остановки.")
    while True:
        event = device.read_one()
        if event:
            print(f"Нажата: {evdev.categorize(event)}")
        time.sleep(0.01)  # небольшая пауза
except KeyboardInterrupt:
    print("\nОстановка по запросу пользователя.")
finally:
    device.close()
    print("Устройство закрыто.")
