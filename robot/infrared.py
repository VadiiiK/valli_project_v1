# работа с инфракрасным пультом
# принимает сигнал и отправляет команда в зависимости от клавиши

import time
import subprocess
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import INFRARED_PIN, INF_BUTTON
from logging_config import logger
from robot.led16_8 import LedShow



class InfraredControl:
    def __init__(self, gpio: GPIOManager):
        self.gpio = gpio
        # self.led16_8 = LedShow()  # Создаём экземпляр
        self.inf_pin = INFRARED_PIN # пин infrared
        self.inf_button = INF_BUTTON # значения кнопки пульта словарь

        # Настройка пина
        self.gpio.setup_input(self.inf_pin, pull_up_down=GPIO.PUD_UP)
        logger.info("[InfraredControl] InfraredControl инициализирован")

    def _check_timeout(self, start_time: float, timeout_s: float) -> bool:
        """Проверяет, превышен ли таймаут."""
        return time.monotonic() - start_time >= timeout_s

    def receive_ir_signal(self, timeout_s=0.1) -> int | None:
        """
        Принимает ИК‑сигнал на пине `self.inf_pin`.
        Возвращает команду (int) или None при ошибке/таймауте.
        """
        start_time = time.monotonic()  # Более точный таймер

        try:
            # 1. Ожидание начала сигнала (переход HIGH → LOW)
            while GPIO.input(self.inf_pin) == GPIO.HIGH:
                if self._check_timeout(start_time, timeout_s):
                    logger.warning("[InfraredControl] Таймаут ожидания начала сигнала")
                    return None
                time.sleep(0.0001)

            # 2. Ожидание стартового LOW (9 мс)
            count = 0
            while GPIO.input(self.inf_pin) == GPIO.LOW:
                count += 1
                if count >= 200 or self._check_timeout(start_time, timeout_s):
                    logger.warning("[InfraredControl] Таймаут стартового LOW")
                    return None
                time.sleep(0.00006)

            # 3. Ожидание стартового HIGH (4.5 мс)
            count = 0
            while GPIO.input(self.inf_pin) == GPIO.HIGH:
                count += 1
                if count >= 80 or self._check_timeout(start_time, timeout_s):
                    logger.warning("[InfraredControl] Таймаут стартового HIGH")
                    return None
                time.sleep(0.00006)

            # 4. Приём 32 бит данных
            data = [0, 0, 0, 0]
            idx, bit_pos = 0, 0

            for _ in range(32):
                # Ожидание LOW (562.5 мкс)
                count = 0
                while GPIO.input(self.inf_pin) == GPIO.LOW:
                    count += 1
                    if count >= 15 or self._check_timeout(start_time, timeout_s):
                        logger.warning("[InfraredControl] Таймаут LOW-импульса")
                        return None
                    time.sleep(0.00006)

                # Ожидание HIGH (определение бита)
                count = 0
                while GPIO.input(self.inf_pin) == GPIO.HIGH:
                    count += 1
                    if count >= 40 or self._check_timeout(start_time, timeout_s):
                        logger.warning("[InfraredControl] Таймаут HIGH-импульса")
                        return None
                    time.sleep(0.00006)

                # Запись бита
                if count > 8:
                    data[idx] |= (1 << bit_pos)

                bit_pos += 1
                if bit_pos == 8:
                    bit_pos = 0
                    idx += 1
                    if idx >= 4:
                        break

            # 5. Проверка контрольных сумм
            if (data[0] + data[1] == 0xFF) and (data[2] + data[3] == 0xFF):
                command = data[2]
                logger.info(f"[InfraredControl] Получена команда: 0x{command:02X}")
                return command
            else:
                logger.error("[InfraredControl] Ошибка: не совпала контрольная сумма")
                return None

        except Exception as e:
            logger.error(f"[InfraredControl] Ошибка приёма ИК‑сигнала: {e}")
            return None

    def exec_cmd(self, command: int) -> bool:
        """
        Обрабатывает полученную команду.
        :param command: код команды (int)
        :return: True, если команда обработана, иначе False
        """
        logger.info(f"[InfraredControl] Выполняется команда: 0x{command:02X}")

        if command in self.inf_button.values():
            button_name = [k for k, v in self.inf_button.items() if v == command][0]
            logger.info(f"[InfraredControl] Нажата кнопка: {button_name}")

            # Пример реакции: мигание светодиода
            print(f"Нажата кнопка: {button_name}")
            # self.led16_8.blink()  # предполагаем, что у LedShow есть метод blink
            return True
        else:
            logger.warning(f"[InfraredControl] Неизвестная команда: 0x{command:02X}")
            return False

    def run(self):
        """Основной цикл приёма команд."""
        logger.info("[InfraredControl] Запуск приёма ИК‑сигналов...")
        try:
            while True:
                command = self.receive_ir_signal(timeout_s=0.5)
                if command is not None:
                    self.exec_cmd(command)
                time.sleep(0.1)  # пауза между приёмами
        except KeyboardInterrupt:
            logger.info("[InfraredControl] Приём ИК‑сигналов остановлен")
        finally:
            self.cleanup()

    def cleanup(self):
        """Освобождает ресурсы GPIO."""
        self.gpio.cleanup(self.inf_pin)  # если в GPIOManager есть такой метод
        logger.info(f"[InfraredControl] GPIO PIN {self.inf_pin} очищены")