import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import time
import RPi.GPIO as GPIO
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