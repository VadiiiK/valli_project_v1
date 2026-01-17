# работа с дисплеем 16*8
# текст в бегущей строке def text to colum, scroll_text

import time
from robot.gpio_manager import GPIOManager
from robot.config import LED16_8_DIO_PIN, LED16_8_SCLK_PIN, FONT_RUS, IMAGE
from logging_config import logger


class LedShow:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio
        self.sclk = LED16_8_SCLK_PIN  # пин SCLK 
        self.dio = LED16_8_DIO_PIN  # пин DIO
        self.font_rus = FONT_RUS # русский алфавит
        self.image = IMAGE

        # Настройка пинов
        self.gpio.setup_output(self.sclk)
        self.gpio.setup_output(self.dio)
        # print(f"[LedShow] Пины настроены: SCLK={self.sclk}, DIO={self.dio}")
        # print(f"[LedShow] SCLK = {self.sclk} (тип: {type(self.sclk)})")
        # print(f"[LedShow] DIO = {self.dio} (тип: {type(self.dio)})")
        logger.info("[LedShow] LedShow инициализирован")
        logger.debug(f"[LedShow] Пины настроены: SCLK={self.sclk}, DIO={self.dio}")
        logger.debug(f"[LedShow] SCLK = {self.sclk} (тип: {type(self.sclk)})")
        logger.debug(f"[LedShow] DIO = {self.dio} (тип: {type(self.dio)})")

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
        self.gpio.output(self.sclk, 1)
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
        # logger.info(f"[LedShow] Запуск дисплея: {data}")
        if not data:
            logger.error("[LedShow] Данные отсутствуют, пропуск")
            return
        
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

        if text is None:
            return columns
        
        if isinstance(text, str):
            text = text.upper()
            for char in text:
                if char in self.font_rus:
                    columns.extend(self.font_rus[char])
                else:
                    # Если символ не найден, добавляем пустое пространство
                    columns.extend([0x00] * 5)
            columns.append(0x00)  # Разделитель
        else:
            # Если text — уже список байтов
            columns.extend(text)
        return columns
    
    def scroll_text(self, text, delay=0.1, loops=3):
        """Бегущая строка: текст движется слева направо"""
        logger.info(f"[LedShow] Запуск бегущей строки <<{text}>>")
        data = self.text_to_columns(text)
        buffer = [0x00] * 16  # Буфер 16 столбцов (ширина матрицы)

        for _ in range(loops * len(data)):  # Ограничиваем число итераций
            # Сдвигаем буфер влево на 1 столбец
            buffer = [0x00] + buffer[:-1]
            
            # Добавляем новый столбец из данных (если есть)
            if len(data) > 0:
                buffer[0] = data[0]
                data = data[1:]
            else:
                # Если текст закончился, начинаем заново
                data = [0x00] * 16
                continue

            self.matrix_display(buffer)
            time.sleep(delay)

    def greeting(self):
        """Демонстрация приветствия"""
        logger.info("[LedShow] Демонстрация <<Приветствия>>")
        keys_smile = ['IMG_SMILE_SLEEP_2', 
                    'IMG_SMILE_SLEEP', 
                    'IMG_SMILE', 
                    'IMG_SMILE_WINK', 
                    'IMG_SMILE_WINK_2', 
                    'IMG_SMILE_WINK', 
                    'IMG_SMILE']
        for key in keys_smile:
            self.matrix_display(self.image[key])
            time.sleep(0.3)
        logger.info("[LedShow] Завершения демонстрации <<Приветствия>>")
        self.matrix_display([0x00] * 16)

    def farewell(self):
        """Демонстрация прощания"""
        logger.info("[LedShow] Демонстрация <<Прощания>>")
        keys_smile = ['IMG_SMILE', 
                    'IMG_SMILE_WINK', 
                    'IMG_SMILE_WINK_2', 
                    'IMG_SMILE_SLEEP', 
                    'IMG_SMILE_SLEEP_2']
        for key in keys_smile:
            self.matrix_display(self.image[key])
            time.sleep(0.3)
        logger.info("[LedShow] Завершения демонстрации <<Прощания>>")
        self.matrix_display([0x00] * 16)


    # Очистка пинов при удалении объекта
    def __del__(self):
        if hasattr(self, 'gpio') and self.gpio is not None:
            self.gpio.cleanup()  # Очистка пинов
            logger.info(f"[LedShow] GPIO PIN {self.sclk}, {self.dio} очищены")
            
    