# работа с инфракрасным пультом
# принимает сигнал и отправляет команда в зависимости от клавиши

import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import INFRARED_PIN, INF_BUTTON
from logging_config import logger
from robot.led16_8 import LedShow



class InfraredControl:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio
        self.led16_8 = LedShow
        self.inf_pin = INFRARED_PIN  # пин infrared
        self.inf_button = INF_BUTTON # значения кнопки пульта словарь

        # Настройка пинов
        self.gpio.setup_input(self.inf_pin, pull_up_down=GPIO.PUD_UP)

    def receive_ir_signal(self, timeout_s=0.1):
        """
        Принимает ИК‑сигнал на пине `self.inf_pin`.
        Возвращает команду (int) или None, если ошибка.
        """
        start_time = time.time()

        try:
            # 1. Ожидание стартового LOW (9 мс)
            count = 0
            while GPIO.input(self.inf_pin) == GPIO.LOW:
                count += 1
                time.sleep(0.00006)
                if count >= 200 or (time.time() - start_time) > timeout_s:
                    return None  # Таймаут

            # 2. Ожидание стартового HIGH (4.5 мс)
            count = 0
            while GPIO.input(self.inf_pin) == GPIO.HIGH:
                count += 1
                time.sleep(0.00006)
                if count >= 80 or (time.time() - start_time) > timeout_s:
                    return None

            # 3. Приём 32 бит
            data = [0, 0, 0, 0]  # 4 байта
            idx = 0  # индекс байта
            bit_pos = 0  # позиция бита в байте (0..7)

            for _ in range(32):
                # Ожидание LOW (562.5 мкс)
                count = 0
                while GPIO.input(self.inf_pin) == GPIO.LOW:
                    count += 1
                    time.sleep(0.00006)
                    if count >= 15 or (time.time() - start_time) > timeout_s:
                        return None

                # Ожидание HIGH (длительность определяет бит)
                count = 0
                while GPIO.input(self.inf_pin) == GPIO.HIGH:
                    count += 1
                    time.sleep(0.00006)
                    if count >= 40 or (time.time() - start_time) > timeout_s:
                        return None

                # Определение бита: >8 → 1, ≤8 → 0
                if count > 8:
                    data[idx] |= (1 << bit_pos)

                # Переход к следующему биту/байту
                bit_pos += 1
                if bit_pos == 8:
                    bit_pos = 0
                    idx += 1
                    if idx >= 4:
                        break  # Получили все 4 байта

            # 4. Проверка контрольных сумм
            if (data[0] + data[1] == 0xFF) and (data[2] + data[3] == 0xFF):
                command = data[2]
                logger.info(f"Получена команда: 0x{command:02X}")
                print(f"Получена команда: 0x{command:02X}")
                return command
            else:
                logger.error("Ошибка: не совпала контрольная сумма")
                print("Ошибка: не совпала контрольная сумма")
                return None

        except Exception as e:
            logger.error(f"Ошибка приёма ИК‑сигнала: {e}")
            print(f"Ошибка приёма ИК‑сигнала: {e}")
            return None
    
    def exec_cmd(self, command):
        """Пример обработчика команд."""
        logger.info(f"Выполняется команда: {command}")
        print(f"Выполняется команда: {command}")
        if command == self.inf_button['Button_*']:
            return 1
        else:
            return 0
