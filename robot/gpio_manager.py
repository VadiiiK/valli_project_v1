# Работа с GPIO
# настройка пинов
# говорит RPi, какие пины будут входами (датчик), а какие — выходами (моторы, серва)

import RPi.GPIO as GPIO

class GPIOManager:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)  # нумерация пинов по BCM
        GPIO.setwarnings(False)    # не показывать предупреждения

    def setup_output(self, pin):
        GPIO.setup(pin, GPIO.OUT)

    def setup_input(self, pin):
        GPIO.setup(pin, GPIO.IN)

    def cleanup(self):
        GPIO.cleanup()  # отключить все пины при завершении


