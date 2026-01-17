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


logger.info("[main] Начинаю инициализацию робота...")
# Создаёт и настраивает компоненты:
# Инициализация GPIO
gpio = GPIOManager()

# Создаём экземпляр LedShow, передавая gpio 
led16_8 = LedShow(gpio)

# Создаём экземпляр LedShow, передавая gpio
inf_control = InfraredControl(gpio, led16_8)

# Приветствие при запуске системы
try:
    logger.info("[Main] Запуск Приветствия")
    led16_8.greeting()
    logger.info("[Main] Завершения Приветствия")
    logger.info("[Main] Начало работы ИК пультом")
    # inf_control.run()
    led16_8.flashing_diode()

except KeyboardInterrupt:
    logger.info("[Main] Прервано пользователем")
    print("Прервано пользователем")

finally:
    led16_8.farewell()
    # Гарантированная очистка
    time.sleep(3)
    led16_8.matrix_display([0x00] * 16)  # Очистить матрицу
    logger.info("[Main] Очистка матрицы")
    gpio.cleanup()
    logger.info("[Main] Завершения кода")
    exit()



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