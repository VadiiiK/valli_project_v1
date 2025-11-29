# работа с дисплеем 16*8
# текст в бегущей строке 

import time
from robot.gpio_manager import GPIOManager
from robot.config import LED16_8_DIO, LED16_8_SCLK


class RunningLine:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio
        self.sclk = LED16_8_SCLK  # пин SCLK 
        self.dio = LED16_8_DIO  # пин DIO 
        gpio.setup_output(self.sclk)
        gpio.setup_output(self.dio)
        gpio.output()

    def nop(self):
        time.sleep(0.00003)

    # начало передачи бит на драйвер
    def start(self): # начало передачи бит на драйвер
        gpio.output(self.sclk, 0)
        self.nop()
        gpio.output(self.sclk, 1)
        self.nop()
        gpio.output(self.dio, 1)
        self.nop()
        gpio.output(self.dio, 0)
        self.nop()

    # конец передачи бит на драйвер
    def end(self):

    