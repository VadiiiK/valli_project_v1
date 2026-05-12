# Импортирует классы из других модулей:
import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.led16_8 import LedShow
from robot.infrared import InfraredControl
import paramiko
import socket
import threading
import os
from logging_config import logger
from robot.actuators import Motor

# Пример использования
if __name__ == "__main__":
    try:
        motor = Motor()
        
        # Тест движения
        motor.set_speed(20)
        motor.forward()
        time.sleep(2)
        
        motor.set_speed(20)
        motor.left()
        time.sleep(2)

        motor.set_speed(20)
        motor.forward_right()
        time.sleep(2)
        
        motor.set_speed(20)
        motor.right()
        time.sleep(2)
        
        motor.set_speed(20)
        motor.backward()
        time.sleep(2)
        
        motor.stop()
        
    except KeyboardInterrupt:
        print("\nПрервано")
    finally:
        motor.cleanup()
        GPIO.cleanup()


# # бегущая строка

# led16_8 = LedShow
# try:
#     led16_8.scroll_text("Привет", delay=0.15)

# except KeyboardInterrupt:
#     print("Прервано пользователем")

# finally:
#     # Гарантированная очистка
#     led16_8.matrix_display([0x00] * 16)  # Очистить матрицу
#     GPIO.cleanup()
#     print("Завершено")







