# Импортирует классы из других модулей:
from robot.gpio_manager import GPIOManager
from robot.led16_8 import RunningLine
import robot.config
# from robot.sensors import DistanceSensor
# from robot.actuators import Motor, Servo
# from robot.navigation import Navigator
# from utils.cli import show_menu

# Создаёт и настраивает компоненты:
# Инициализация GPIO

# Инициализация GPIO
gpio = GPIOManager()

# Создаём экземпляр RunningLine, передавая gpio 
running_line = RunningLine(gpio) 

# Текст или изображение для отображения
TEXT = robot.config.IMG_HEART  # Убедитесь, что это список байтов


try:
    running_line.scroll_text("Привет", delay=0.15)

except KeyboardInterrupt:
    print("Прервано пользователем")

finally:
    # Гарантированная очистка
    running_line.matrix_display([0x00] * 16)  # Очистить матрицу
    gpio.cleanup()
    print("Завершено")


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