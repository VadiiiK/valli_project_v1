# работа с инфракрасным пультом
# принимает сигнал и отправляет команда в зависимости от клавиши

import time
import subprocess
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import INFRARED_PIN, INF_BUTTON, MENU_LIST
from logging_config import logger
from robot.led16_8 import LedShow



class InfraredControl:
    def __init__(self, gpio: GPIOManager, led16_8: LedShow):
        self.gpio = gpio
        self.led16_8 = led16_8  # Создаём экземпляр
        self.inf_pin = INFRARED_PIN # пин infrared
        self.inf_button = INF_BUTTON # значения кнопки пульта словарь
        self.menu_list = MENU_LIST # список меню

        # Настройка пина
        self.gpio.setup_input(self.inf_pin, pull_up_down=GPIO.PUD_UP)

        # Для отслеживания тройного нажатия
        self.hash_press_times = []  # список времён нажатий #
        self.hash_timeout = 2.0  # сек: за какое время должны быть 3 нажатия
        self.hash_max_count = 3   # сколько нажатий нужно
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

        # Ищем имя кнопки по коду
        button_name = None
        for k, v in self.inf_button.items():
            if v == command:
                button_name = k
                break

        if button_name is None:
            logger.warning(f"[InfraredControl] Неизвестная команда: 0x{command:02X}")
            return False

        logger.info(f"[InfraredControl] Нажата кнопка: {button_name.upper()}")
        print(f"Нажата кнопка: {button_name.upper()}")

        # Обработка кнопки #
        if button_name == "Button_#":
            # Добавляем время текущего нажатия
            self.hash_press_times.append(time.time())

            # Оставляем только нажатия за последние `hash_timeout` секунд
            now = time.time()
            self.hash_press_times = [
                t for t in self.hash_press_times if now - t <= self.hash_timeout
            ]

            # Если накопилось 3 нажатия — выключаем RPi
            if len(self.hash_press_times) >= self.hash_max_count:
                logger.info("[InfraredControl] Обнаружено тройное нажатие # — выключение RPi")
                print("Тройное нажатие # — выключаю Raspberry Pi...")
                self._shutdown_rpi()
                # Очищаем список, чтобы не срабатывало повторно
                self.hash_press_times.clear()
                return True

            return True  # обработано, но не 3 раза

        # Здесь можно добавить обработку других кнопок
        # elif button_name == "Power":
        # Обработка кнопки *
        elif button_name == "Button_*":
            # Добавляем время текущего нажатия
            self.hash_press_times.append(time.time())
        
            # Оставляем только нажатия за последние `hash_timeout` секунд
            now = time.time()
            self.hash_press_times = [
                t for t in self.hash_press_times if now - t <= self.hash_timeout
            ]

            # Если накопилось 3 нажатия — перезагружаем RPi
            if len(self.hash_press_times) >= self.hash_max_count:
                logger.info("[InfraredControl] Обнаружено тройное нажатие * — перезагрузка RPi")
                print("Тройное нажатие * — перезагружаю Raspberry Pi...")
                self._menu()
                # Очищаем список, чтобы не срабатывало повторно
                self.hash_press_times.clear()
                return True
            
            return True  # обработано, но не 3 раза

        else:
            # Для остальных кнопок — просто отмечаем нажатие
            return True


    def _shutdown_rpi(self):
        """Выполняет команду выключения Raspberry Pi."""
        try:
            logger.info("Выполняю команду: sudo shutdown -h now")
            self.led16_8.scroll_text("ВЫКЛЮЧЕНИЕ", delay=0.15)
            self.led16_8.matrix_display([0x00] * 16)  # Очистить матрицу
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при выключении RPi: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при выключении RPi: {e}")


    def _reboot_rpi(self):
        """Выполняет команду перезагрузки Raspberry Pi."""
        try:
            logger.info("Выполняю команду: sudo reboot")
            self.led16_8.scroll_text("ПЕРЕЗАГРУЗКА", delay=0.15)
            self.led16_8.matrix_display([0x00] * 16)  # Очистить матрицу
            subprocess.run(["sudo", "reboot"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при перезагрузке RPi: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при перезагрузке RPi: {e}")


    def _menu(self):
        try:
            logger.info("Выполняю команду: menu")
            self.led16_8.scroll_text(self.menu_list, delay=0.1)

        except Exception as e:
            logger.error(f"Неожиданная ошибка при вызове меню: {e}")
            LedShow.matrix_display([0x00] * 16)  # Очистить матрицу
        

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