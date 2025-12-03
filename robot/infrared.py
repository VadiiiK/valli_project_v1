# работа с инфракрасным пультом
# принимает сигнал и отправляет команда в зависимости от клавиши

import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import INFRARED_PIN, INF_BUTTON


class InfraredControl:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio
        self.inf_pin = INFRARED_PIN  # пин infrared
        self.inf_button = INF_BUTTON # значения кнопки пульта словарь

        # Настройка пинов
        self.gpio.setup_input(self.inf_pin, pull_up_down=GPIO.PUD_UP)
        