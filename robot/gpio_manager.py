# Работа с GPIO
# настройка пинов
# говорит RPi, какие пины будут входами (датчик), а какие — выходами (моторы, серва)

import RPi.GPIO as GPIO


class GPIOManager:
    """
    Менеджер для работы с пинами GPIO на Raspberry Pi.
    Инкапсулирует вызовы RPi.GPIO, обеспечивая безопасный интерфейс.
    """
    
    def __init__(self, mode=GPIO.BCM, warnings=False):
        """
        Инициализирует менеджер GPIO.
        
        :param mode: режим нумерации пинов (GPIO.BCM или GPIO.BOARD)
        :param warnings: показывать предупреждения GPIO (True/False)
        """
        GPIO.setmode(mode)
        GPIO.setwarnings(warnings)
        self.mode = mode

    def setup_output(self, pin):
        """
        Настраивает пин как выход.
        
        :param pin: номер пина (int)
        :raises ValueError: если пин невалидный
        :raises RuntimeError: если ошибка конфигурации
        """
        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"Некорректный пин: {pin}. Должен быть положительным целым числом.")
        
        try:
            GPIO.setup(pin, GPIO.OUT)
            print(f"[GPIOManager] Пин {pin} настроен как OUTPUT")
        except Exception as e:
            raise RuntimeError(f"Ошибка настройки пина {pin} как выхода: {e}")

    def setup_input(self, pin):
        """
        Настраивает пин как вход.
        
        :param pin: номер пина (int)
        :raises ValueError: если пин невалидный
        :raises RuntimeError: если ошибка конфигурации
        """
        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"Некорректный пин: {pin}. Должен быть положительным целым числом.")
        
        try:
            GPIO.setup(pin, GPIO.IN)
        except Exception as e:
            raise RuntimeError(f"Ошибка настройки пина {pin} как входа: {e}")

    def output(self, pin, value):
        """
        Устанавливает уровень на пине (HIGH/LOW).
        
        :param pin: номер пина (int)
        :param value: GPIO.HIGH или GPIO.LOW (или 1/0)
        :raises ValueError: если пин или значение невалидные
        :raises RuntimeError: если ошибка установки
        """
        # Явная проверка режима нумерации
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)  # или GPIO.BOARD

        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"Некорректный пин: {pin}.")
        
        if value not in (GPIO.HIGH, GPIO.LOW, 1, 0):
            raise ValueError(f"Некорректное значение: {value}. Должно быть GPIO.HIGH, GPIO.LOW, 1 или 0.")
        
        try:
            GPIO.output(pin, value)
        except Exception as e:
            raise RuntimeError(f"Ошибка установки значения {value} на пине {pin}: {e}")

    def input(self, pin):
        """
        Считывает уровень на пине.
        
        :param pin: номер пина (int)
        :return: GPIO.HIGH или GPIO.LOW
        :raises ValueError: если пин невалидный
        :raises RuntimeError: если ошибка чтения
        """
        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"Некорректный пин: {pin}.")
        
        try:
            return GPIO.input(pin)
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения пина {pin}: {e}")

    def cleanup(self):
        """
        Отключает все пины GPIO и освобождает ресурсы.
        Вызывайте при завершении работы.
        """
        GPIO.cleanup()






