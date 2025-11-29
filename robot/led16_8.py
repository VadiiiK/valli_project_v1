# работа с дисплеем 16*8
# текст в бегущей строке 

import time
from robot.gpio_manager import GPIOManager
from robot.config import LED16_8_DIO, LED16_8_SCLK, FONT_RUS, IMG_HEART


class RunningLine:
    def __init__(self, gpio: GPIOManager, pin: int, value):
        self.gpio = gpio
        self.sclk = LED16_8_SCLK  # пин SCLK 
        self.dio = LED16_8_DIO  # пин DIO
        self.font_rus = FONT_RUS # русский алфавит
        self.img_heart = IMG_HEART # картинка сердце
        gpio.setup_output(self.sclk)
        gpio.setup_output(self.dio)
        

    def nop(self):
        time.sleep(0.00003)

    # начало передачи бит на драйвер
    def start(self): # начало передачи бит на драйвер
        self.gpio.output(self.sclk, 0)
        self.nop()
        self.gpio.output(self.sclk, 1)
        self.nop()
        self.gpio.output(self.dio, 1)
        self.nop()
        self.gpio.output(self.dio, 0)
        self.nop()

    # конец передачи бит на драйвер
    def end(self):
        self.gpio.output(self.sclk, 0)
        self.nop()
        self.gpio.output(self.dio, 0)
        self.nop()
        self.gpio.output(self.sllk, 1)
        self.nop()
        self.gpio.output(self.dio, 1)
        self.nop()

    # проверка байта
    def send_byte(self, byte):  
        for _ in range(8):
            self.gpio.output(self.sclk, 0)
            self.nop()
            if byte & 0x01: # проверяет, установлен ли младший (нулевой) бит в переменной 
                self.gpio.output(self.dio, 1)
            else:
                self.gpio.output(self.dio, 0)
            self.nop()
            self.gpio.output(self.sclk, 1)
            self.nop()
            byte >>= 1 # сдвинуть все биты переменной byte вправо на 1 позицию, затем сохранить результат обратно
            self.gpio.output(self.sclk, 0)

    # старт дисплея
    def matrix_display(self, data):
        self.start()
        self.send_byte(0xC0)  # Команда записи в память
        for byte in data:
            self.send_byte(byte)
        self.end()
        self.start()
        self.send_byte(0x8A)  # Яркость (уровень 10)
        self.end()

    def text_to_columns(self, text): 
        """Преобразует текст в последовательность столбцов для скролла"""
        columns = []
        if type(text) == str:
            for char in text:
                if char in self.font_rus:
                    columns.extend(self.font_rus[char])
                else:
                    if type(char) == list:
                        columns.extend(char)
                    else:
                        columns.extend([0x00] * 5)  # Неизвестный символ → пусто
            columns.append(0x00)  # Разделитель между символами
        else:
            columns.extend(text)

        return columns
    
    def scroll_text(self, text, delay=0.2):
        """Бегущая строка: текст движется слева направо"""
        data = self.text_to_columns(text)
        buffer = [0x00] * 16  # Буфер 16 столбцов (ширина матрицы)


        while True:
            # Сдвигаем буфер влево на 1 столбец
            buffer = [0x00] + buffer[:-1]
            
            # Добавляем новый столбец из данных (если есть)
            if len(data) > 0:
                buffer[0] = data[0]
                data = data[1:]
            else:
                # Если текст закончился, начинаем заново
                data = self.text_to_columns(text)
                continue

            self.matrix_display(buffer)
            time.sleep(delay)

    