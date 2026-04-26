# управление моторами/сервами (через GPIO)
# Мотор (с PWM)
# меняет скорость вращения через сигнал PWM (широтно‑импульсная модуляция)
# Для движения назад нужен H‑мост (специальная микросхема), иначе мотор не развернётся

import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import M1_RL_PIN1, M1_RL_PIN2, M1_RL_PWR, M2_FL_PIN1, M2_FL_PIN2, M2_FL_PWR, M3_FR_PIN1, M3_FR_PIN2, M3_FR_PWR, M4_RR_PIN1, M4_RR_PIN2, M4_RR_PWR, MOTOR_FREQ
from logging_config import logger

class Motor:
    def __init__(self):
        self.gpio = GPIOManager()
        
        # Настройка пинов для левых моторов
        self.gpio.setup_output(M1_RL_PIN1)
        self.gpio.setup_output(M1_RL_PIN2)
        self.gpio.setup_output(M1_RL_PWR)
        
        self.gpio.setup_output(M2_FL_PIN1)
        self.gpio.setup_output(M2_FL_PIN2)
        self.gpio.setup_output(M2_FL_PWR)
        
        # Настройка пинов для правых моторов
        self.gpio.setup_output(M3_FR_PIN1)
        self.gpio.setup_output(M3_FR_PIN2)
        self.gpio.setup_output(M3_FR_PWR)
        
        self.gpio.setup_output(M4_RR_PIN1)
        self.gpio.setup_output(M4_RR_PIN2)
        self.gpio.setup_output(M4_RR_PWR)
        
        # Инициализация PWM с частотой MOTOR_FREQ
        self.pwm_LL = GPIO.PWM(M1_RL_PWR, MOTOR_FREQ)  # Левый левый
        self.pwm_LR = GPIO.PWM(M2_FL_PWR, MOTOR_FREQ)  # Правый левый
        self.pwm_RL = GPIO.PWM(M3_FR_PWR, MOTOR_FREQ)  # Левый правый
        self.pwm_RR = GPIO.PWM(M4_RR_PWR, MOTOR_FREQ)  # Правый правый
        
        # Запуск PWM с 0% duty cycle
        self.pwm_LL.start(0)
        self.pwm_LR.start(0)
        self.pwm_RL.start(0)
        self.pwm_RR.start(0)
        
        # Скорость по умолчанию (0-100%)
        self.default_speed = 70
        
        logger.info("[Motor] Motor инициализирован")
    
    def _set_motor_speed(self, pwm, speed):
        """Установка скорости для одного мотора"""
        speed = max(0, min(100, speed))  # Ограничиваем 0-100%
        pwm.ChangeDutyCycle(speed)
    
    def _set_motors(self, left_speed, right_speed):
        """Установка скорости для левых и правых моторов"""
        # Левые моторы (M1 и M2)
        self._set_motor_speed(self.pwm_LL, left_speed)
        self._set_motor_speed(self.pwm_LR, left_speed)
        
        # Правые моторы (M3 и M4)
        self._set_motor_speed(self.pwm_RL, right_speed)
        self._set_motor_speed(self.pwm_RR, right_speed)
    
    def _set_direction(self, left_forward, right_forward):
        """Установка направления движения"""
        # Левые моторы
        if left_forward:
            self.gpio.output(M1_RL_PIN1, 1)
            self.gpio.output(M1_RL_PIN2, 0)
            self.gpio.output(M2_FL_PIN1, 0)
            self.gpio.output(M2_FL_PIN2, 1)
        else:
            self.gpio.output(M1_RL_PIN1, 0)
            self.gpio.output(M1_RL_PIN2, 1)
            self.gpio.output(M2_FL_PIN1, 1)
            self.gpio.output(M2_FL_PIN2, 0)
        
        # Правые моторы
        if right_forward:
            self.gpio.output(M3_FR_PIN1, 1)
            self.gpio.output(M3_FR_PIN2, 0)
            self.gpio.output(M4_RR_PIN1, 0)
            self.gpio.output(M4_RR_PIN2, 1)
        else:
            self.gpio.output(M3_FR_PIN1, 0)
            self.gpio.output(M3_FR_PIN2, 1)
            self.gpio.output(M4_RR_PIN1, 1)
            self.gpio.output(M4_RR_PIN2, 0)
    
    def stop(self):
        """Остановка всех моторов"""
        print("🛑 СТОП")
        self._set_motors(0, 0)
        self.gpio.output(M1_RL_PIN1, 0)
        self.gpio.output(M1_RL_PIN2, 0)
        self.gpio.output(M2_FL_PIN1, 0)
        self.gpio.output(M2_FL_PIN2, 0)
        self.gpio.output(M3_FR_PIN1, 0)
        self.gpio.output(M3_FR_PIN2, 0)
        self.gpio.output(M4_RR_PIN1, 0)
        self.gpio.output(M4_RR_PIN2, 0)
    
    def forward(self):
        """Движение вперёд"""
        print("⬆️  ВПЕРЁД")
        self._set_direction(True, True)
        self._set_motors(self.default_speed, self.default_speed)
    
    def backward(self):
        """Движение назад"""
        print("⬇️  НАЗАД")
        self._set_direction(False, False)
        self._set_motors(self.default_speed, self.default_speed)
    
    def left(self):
        """Поворот налево (левые колёса назад, правые вперёд)"""
        print("⬅️  ВЛЕВО")
        self._set_direction(False, True)  # Левые назад, правые вперёд
        self._set_motors(self.default_speed, self.default_speed)
    
    def right(self):
        """Поворот направо (левые вперёд, правые назад)"""
        print("➡️  ВПРАВО")
        self._set_direction(True, False)  # Левые вперёд, правые назад
        self._set_motors(self.default_speed, self.default_speed)
    
    def forward_left(self):
        """Плавный поворот налево вперёд"""
        print("↖️  ВЛЕВО-ВПЕРЁД")
        self._set_direction(True, True)
        self._set_motors(self.default_speed // 2, self.default_speed)
    
    def forward_right(self):
        """Плавный поворот направо вперёд"""
        print("↗️  ВПРАВО-ВПЕРЁД")
        self._set_direction(True, True)
        self._set_motors(self.default_speed, self.default_speed // 2)
    
    def backward_left(self):
        """Плавный поворот налево назад"""
        print("↙️  ВЛЕВО-НАЗАД")
        self._set_direction(False, False)
        self._set_motors(self.default_speed // 2, self.default_speed)
    
    def backward_right(self):
        """Плавный поворот направо назад"""
        print("↘️  ВПРАВО-НАЗАД")
        self._set_direction(False, False)
        self._set_motors(self.default_speed, self.default_speed // 2)
    
    def set_speed(self, speed: int):
        """Установка скорости для всех моторов (0-100)"""
        self.default_speed = max(0, min(100, speed))
        print(f"⚡ Скорость установлена: {self.default_speed}%")
    
    def set_speed_left_right(self, left_speed: int, right_speed: int):
        """Раздельная установка скорости для левых и правых моторов"""
        left_speed = max(0, min(70, left_speed))
        right_speed = max(0, min(70, right_speed))
        self._set_motors(left_speed, right_speed)
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop()
        self.pwm_LL.stop()
        self.pwm_LR.stop()
        self.pwm_RL.stop()
        self.pwm_RR.stop()
        logger.info("[Motor] Motor очищен")

# # Пример использования
# if __name__ == "__main__":
#     try:
#         motor = Motor()
        
#         # Тест движения
#         motor.forward()
#         time.sleep(2)
        
#         motor.left()
#         time.sleep(1)
        
#         motor.right()
#         time.sleep(1)
        
#         motor.backward()
#         time.sleep(2)
        
#         motor.stop()
        
#     except KeyboardInterrupt:
#         print("\nПрервано")
#     finally:
#         motor.cleanup()
#         GPIO.cleanup()