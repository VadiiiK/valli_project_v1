# управление моторами/сервами (через GPIO)
# Мотор (с PWM)
# меняет скорость вращения через сигнал PWM (широтно‑импульсная модуляция)
# Для движения назад нужен H‑мост (специальная микросхема), иначе мотор не развернётся

import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import M1_L_PIN1, M1_L_PIN2, M1_L_PWR, M2_L_PIN1, M2_L_PIN2, M2_L_PWR, M3_R_PIN1, M3_R_PIN2, M3_R_PWR, M4_R_PIN1, M4_R_PIN2, M4_R_PWR, MOTOR_FREQ
from logging_config import logger

class Motor:
    def __init__(self):
        self.gpio = GPIOManager
        # #set the MOTOR Driver Pin OUTPUT mode
        # self.gpio.setup_output(M1_L_PIN1)
        # self.gpio.setup_output(M1_L_PIN2)
        # self.gpio.setup_output(M1_L_PWR)

        # self.gpio.setup_output(M2_L_PIN1)
        # self.gpio.setup_output(M2_L_PIN2)
        # self.gpio.setup_output(M2_L_PWR)
        
        # self.gpio.setup_output(M3_R_PIN1)
        # self.gpio.setup_output(M3_R_PIN2)
        # self.gpio.setup_output(M3_R_PWR)

        # self.gpio.setup_output(M4_R_PIN1)
        # self.gpio.setup_output(M4_R_PIN2)
        # self.gpio.setup_output(M4_R_PWR)
        # #set pwm frequence to 1000hz
        # self.pwm_R1 = GPIO.PWM(M1_L_PWR, MOTOR_FREQ)
        # self.pwm_R2 = GPIO.PWM(M2_L_PWR, MOTOR_FREQ)
        # self.pwm_L1 = GPIO.PWM(M3_R_PWR, MOTOR_FREQ)
        # self.pwm_L2 = GPIO.PWM(M4_R_PWR, MOTOR_FREQ)

        # logger.info("[Motor] Motor инициализирован")
        
    def stop(self):
        print("^^^СТОП^^^")
        # self.gpio.output(M1_L_PIN1, 0)
        # self.gpio.output(M1_L_PIN2, 0)
        # self.gpio.output(M2_L_PIN1, 0)
        # self.gpio.output(M2_L_PIN2, 0)
        # self.gpio.output(M3_R_PIN1, 0)
        # self.gpio.output(M3_R_PIN2, 0)
        # self.gpio.output(M4_R_PIN1, 0)
        # self.gpio.output(M4_R_PIN2, 0)

    def forward(self):
        print("^^^ВПЕРД ЕДЕМ^^^")
        # self.stop()
        # self.gpio.output(M1_L_PIN2, 1)
        # self.gpio.output(M2_L_PIN2, 1)
        # self.gpio.output(M3_R_PIN2, 1)
        # self.gpio.output(M4_R_PIN2, 1)

    def backward(self):
        print("^^^НАЗАД ЕДЕМ^^^")
        # self.stop()
        # self.gpio.output(M1_L_PIN1, 1)
        # self.gpio.output(M2_L_PIN1, 1)
        # self.gpio.output(M3_R_PIN1, 1)
        # self.gpio.output(M4_R_PIN1, 1)

    def left(self):
        print("^^^НА ЛЕВО ЕДЕМ^^^")
        # self.stop()
        # self.gpio.output(M3_R_PIN1, 1)
        # self.gpio.output(M4_R_PIN1, 1) 

    def right(self):
        print("^^^НА ПРАВО ЕДЕМ^^^")
        # self.stop()
        # self.gpio.output(M1_L_PIN1, 1)
        # self.gpio.output(M2_L_PIN1, 1)        
    
    def set_speed(self, speed: int):
        """speed: от -100 (назад) до 100 (вперёд)"""
        if speed == 0:
            self.pwm.ChangeDutyCycle(0)
        elif speed > 0:
            duty = min(speed, 100)
            self.pwm.ChangeDutyCycle(duty)
        else:
            # Для реверса нужен отдельный пин направления или H‑мост
            print("Реверс не реализован (требуется H‑мост)")


# Сервопривод
# поворачивает вал на заданный угол (0–180°).


# from robot.gpio_manager import GPIOManager
# from robot.config import SERVO_PIN, SERVO_FREQ


# class Servo:
#     def __init__(self, gpio: GPIOManager):
#         self.gpio = gpio
#         self.gpio.setup_output(SERVO_PIN)
#         self.pwm = GPIO.PWM(SERVO_PIN, SERVO_FREQ)
#         self.pwm.start(0)

#     def set_angle(self, angle: int):
#         """angle: 0–180 градусов"""
#         if 0 <= angle <= 180:
#             # Расчёт коэффициента заполнения (пример для SG90)
#             duty = 2 + (angle / 18)
#             self.pwm.ChangeDutyCycle(duty)
#             time.sleep(0.1)  # ждём поворота
#             self.pwm.ChangeDutyCycle(0)  # отключаем сигнал
#         else:
#             print("Угол должен быть 0–180°")