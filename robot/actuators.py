# управление моторами/сервами (через GPIO)
# Мотор (с PWM)
# меняет скорость вращения через сигнал PWM (широтно‑импульсная модуляция)
# Для движения назад нужен H‑мост (специальная микросхема), иначе мотор не развернётся

import time
from robot.gpio_manager import GPIOManager
from robot.config import MOTOR_LEFT_PIN, MOTOR_RIGHT_PIN, MOTOR_FREQ

class Motor:
    def __init__(self, gpio: GPIOManager, pin: int):
        self.gpio = gpio
        self.pin = pin
        self.gpio.setup_output(pin)
        self.pwm = GPIO.PWM(pin, MOTOR_FREQ)
        self.pwm.start(0)  # старт с 0%

    def set_speed(self, speed: int):
        """speed: от -100 (назад) до 100 (вперёд)"""
        if speed == 0:
            self.pwm.ChangeDutyCycle(0)
        elif speed > 0:
            duty = min(speed, 100)
            self.pwm.ChangeDutyCycle(duty)
        else:
            # Для реверса нужен отдельный пин направления или H‑мост
            print("Реверс не реализован (требуется H‑мост)")


# Сервопривод
# поворачивает вал на заданный угол (0–180°).


from robot.gpio_manager import GPIOManager
from robot.config import SERVO_PIN, SERVO_FREQ


class Servo:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio
        self.gpio.setup_output(SERVO_PIN)
        self.pwm = GPIO.PWM(SERVO_PIN, SERVO_FREQ)
        self.pwm.start(0)

    def set_angle(self, angle: int):
        """angle: 0–180 градусов"""
        if 0 <= angle <= 180:
            # Расчёт коэффициента заполнения (пример для SG90)
            duty = 2 + (angle / 18)
            self.pwm.ChangeDutyCycle(duty)
            time.sleep(0.1)  # ждём поворота
            self.pwm.ChangeDutyCycle(0)  # отключаем сигнал
        else:
            print("Угол должен быть 0–180°")