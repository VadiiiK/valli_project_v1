# чтение датчика расстояния

import time
from robot.gpio_manager import GPIOManager


class DistanceSensor:
    def __init__(self, gpio):
        self.gpio = gpio
        self.trig = 23  # пин Trig датчика
        self.echo = 24  # пин Echo датчика
        gpio.setup_output(self.trig)
        gpio.setup_input(self.echo)

    def get_distance(self):
        # Посылаем импульс
        GPIO.output(self.trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trig, GPIO.LOW)

        # Ждём ответ
        while GPIO.input(self.echo) == 0:
            start = time.time()
        while GPIO.input(self.echo) == 1:
            end = time.time()

        # Считаем расстояние
        duration = end - start
        distance = (duration * 34300) / 2  # 343 м/с — скорость звука
        return round(distance, 1)
    


# import time
# from robot.gpio_manager import GPIOManager
# from robot.config import SENSOR_TRIG_PIN, SENSOR_ECHO_PIN, SENSOR_TIMEOUT

# class DistanceSensor:
#     def __init__(self, gpio: GPIOManager):
#         self.gpio = gpio
#         self.gpio.setup_output(SENSOR_TRIG_PIN)
#         self.gpio.setup_input(SENSOR_ECHO_PIN)

#     def get_distance(self) -> float:
#         # Отправляем импульс
#         GPIO.output(SENSOR_TRIG_PIN, GPIO.HIGH)
#         time.sleep(0.00001)
#         GPIO.output(SENSOR_TRIG_PIN, GPIO.LOW)

#         # Ждём эхо
#         start_time = time.time()
#         while GPIO.input(SENSOR_ECHO_PIN) == 0:
#             start_time = time.time()
#             if start_time - time.time() > SENSOR_TIMEOUT:
#                 return -1  # ошибка

#         while GPIO.input(SENSOR_ECHO_PIN) == 1:
#             end_time = time.time()
#             if end_time - start_time > SENSOR_TIMEOUT:
#                 return -1

#         # Расчёт дистанции
#         duration = end_time - start_time
#         distance = (duration * 34300) / 2  # см (скорость звука 343 м/с)
#         return round(distance, 2)

#     def is_obstacle(self) -> bool:
#         dist = self.get_distance()
#         return dist > 0 and dist < SENSOR_THRESHOLD