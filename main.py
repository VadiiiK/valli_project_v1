# Импортирует классы из других модулей:
from logging_config import logger
from robot.gpio_manager import GPIOManager
from robot.led16_8 import LedShow
from robot.infrared import InfraredControl
import robot.config
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
running_line = LedShow(gpio)

# Создаём экземпляр LedShow, передавая gpio
inf_control = InfraredControl(gpio)

# Текст или изображение для отображения
smiles = robot.config.IMAGE

# Приветствие при запуске системы
try:
    logger.info("[main] Запуск Приветствия")
    keys_smile = ['IMG_SMILE_SLEEP_2', 
                 'IMG_SMILE_SLEEP', 
                 'IMG_SMILE', 
                 'IMG_SMILE_WINK', 
                 'IMG_SMILE_WINK_2', 
                 'IMG_SMILE_WINK', 
                 'IMG_SMILE']
    for key in keys_smile:
        running_line.matrix_display(smiles[key])
        time.sleep(0.3)
    logger.info("[main] Завершения Приветствия")
    
    logger.info("[main] Начало работы ИК пультом")
    command = inf_control.run()
    #     if command is not None:

    #             print(f"Команда: {command} не соответствует!")
    #     time.sleep(0.1)  # пауза между приёмами

except KeyboardInterrupt:
    logger.info("[main] Прервано пользователем")
    print("Прервано пользователем")

finally:
    # Гарантированная очистка
    time.sleep(3)
    running_line.matrix_display([0x00] * 16)  # Очистить матрицу
    logger.info("[main] Очистка матрицы")
    gpio.cleanup()
    logger.info("[main] Завершения кода")
    exit()



# бегущая строка
# try:
#     running_line.scroll_text("Привет", delay=0.15)

# except KeyboardInterrupt:
#     print("Прервано пользователем")

# finally:
#     # Гарантированная очистка
#     running_line.matrix_display([0x00] * 16)  # Очистить матрицу
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