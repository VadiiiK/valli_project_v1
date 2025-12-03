# Работа с GPIO
# настройка пинов
# говорит RPi, какие пины будут входами (датчик), а какие — выходами (моторы, серва)

import RPi.GPIO as GPIO
from logging_config import logger


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
            logger.debug(f"[GPIOManager] Пин {pin} настроен как OUTPUT")
            print(f"[GPIOManager] Пин {pin} настроен как OUTPUT")
        except Exception as e:
            err_msg = f"Ошибка настройки пина {pin} как выхода: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    def setup_input(self, pin, pull_up_down=None):
        """
        Настраивает пин как вход с опциональной подтяжкой.

        :param pin: номер пина (int)
        :param pull_up_down: режим подтяжки (GPIO.PUD_UP, GPIO.PUD_DOWN или None)
        :raises ValueError: если пин или параметр подтяжки невалидные
        :raises RuntimeError: если ошибка конфигурации
        """
        if not isinstance(pin, int) or pin < 0:
            logger.error(f"Некорректный пин: {pin}. Должен быть положительным целым числом.") 
            raise ValueError(f"Некорректный пин: {pin}. Должен быть положительным целым числом.")

        # Проверка допустимости параметра pull_up_down
        if pull_up_down not in (None, GPIO.PUD_UP, GPIO.PUD_DOWN):
            logger.error(f"Некорректный режим подтяжки: {pull_up_down}. "
                         f"Используйте GPIO.PUD_UP, GPIO.PUD_DOWN или None."
                         )
            raise ValueError(
                f"Некорректный режим подтяжки: {pull_up_down}. "
                f"Используйте GPIO.PUD_UP, GPIO.PUD_DOWN или None."
            )

        try:
            # Если подтяжка не указана — передаём только GPIO.IN
            if pull_up_down is None:
                GPIO.setup(pin, GPIO.IN)
            else:
                GPIO.setup(pin, GPIO.IN, pull_up_down)
            
            # Логирование с указанием режима подтяжки
            pull_str = "без подтяжки" if pull_up_down is None else \
                       "PUD_UP" if pull_up_down == GPIO.PUD_UP else "PUD_DOWN"
            logger.debug(f"[GPIOManager] Пин {pin} настроен как INPUT ({pull_str})")
            print(f"[GPIOManager] Пин {pin} настроен как INPUT ({pull_str})")

        except Exception as e:
            logger.error(f"Ошибка настройки пина {pin} как входа: {e}")
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
            logger.error(f"Некорректное значение: {value}. Должно быть GPIO.HIGH, GPIO.LOW, 1 или 0.")
            raise ValueError(f"Некорректное значение: {value}. Должно быть GPIO.HIGH, GPIO.LOW, 1 или 0.")
        
        try:
            GPIO.output(pin, value)
        except Exception as e:
            logger.error(f"Ошибка установки значения {value} на пине {pin}: {e}")
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
            logger.error(f"Некорректный пин: {pin}.")
            raise ValueError(f"Некорректный пин: {pin}.")
        
        try:
            return GPIO.input(pin)
        except Exception as e:
            logger.error(f"Ошибка чтения пина {pin}: {e}")
            raise RuntimeError(f"Ошибка чтения пина {pin}: {e}")

    def cleanup(self):
        """
        Отключает все пины GPIO и освобождает ресурсы.
        Вызывайте при завершении работы.
        """
        GPIO.cleanup()






