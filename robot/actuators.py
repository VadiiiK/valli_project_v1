# управление моторами/сервами (через GPIO)
# Мотор (с PWM)
# меняет скорость вращения через сигнал PWM (широтно‑импульсная модуляция)
# Для движения назад нужен H‑мост (специальная микросхема), иначе мотор не развернётся

import time
import RPi.GPIO as GPIO
from robot.gpio_manager import GPIOManager
from robot.config import MOTORS, MOTOR_FREQ, SOFT_START_TIME
from logging_config import logger

class Motor:
    def __init__(self):
        self.gpio = GPIOManager()
        self.pwm_objects = {}  # Словарь для хранения PWM объектов
        self.motor_config = MOTORS  # Сохраняем конфигурацию
        
        # 1. Настройка всех пинов через словарь
        for motor_name, pins in MOTORS.items():
            # Настройка каждого пина мотора
            self.gpio.setup_output(pins['pin1'])
            self.gpio.setup_output(pins['pin2'])
            self.gpio.setup_output(pins['pwr'])
            logger.debug(f"[Motor] Настроены пины для {motor_name}: {pins}")
        
        # 2. Создание и запуск PWM с плавным пуском для каждого мотора
        for motor_name, pins in MOTORS.items():
            pwm = GPIO.PWM(pins['pwr'], MOTOR_FREQ)
            pwm.start(0)  # Запускаем с 0%
            
            # Плавный пуск (soft start)
            logger.info(f"[Motor] Плавный пуск {motor_name}...")
            for duty_cycle in range(0, 31, 5):  # 0% -> 30% с шагом 5%
                pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(SOFT_START_TIME / 6)  # Делим время на 6 шагов
            
            # Возвращаем на 0%
            pwm.ChangeDutyCycle(0)
            self.pwm_objects[motor_name] = pwm
            logger.info(f"[Motor] {motor_name} готов (PWM на {pins['pwr']})")
        
        # 3. Сохраняем ссылки на PWM для удобства (по старой логике)
        motor_list = list(MOTORS.keys())
        self.pwm_LL = self.pwm_objects[motor_list[0]]  # M1_RL
        self.pwm_LR = self.pwm_objects[motor_list[1]]  # M2_FL
        self.pwm_RL = self.pwm_objects[motor_list[2]]  # M3_FR
        self.pwm_RR = self.pwm_objects[motor_list[3]]  # M4_RR
        
        # Скорость по умолчанию (0-100%)
        self.default_speed = 75
        
        logger.info("[Motor] Все моторы инициализированы с плавным пуском")
    
    def _set_motor_speed(self, motor_name, speed):
        """Установка скорости для одного мотора по имени"""
        speed = max(0, min(100, speed))
        if motor_name in self.pwm_objects:
            self.pwm_objects[motor_name].ChangeDutyCycle(speed)
    
    def _set_motors(self, left_speed, right_speed):
        """Установка скорости для левых и правых моторов"""
        motor_list = list(MOTORS.keys())
        # Левые моторы (M1_RL и M2_FL) - первые два в словаре
        self._set_motor_speed(motor_list[0], left_speed)
        self._set_motor_speed(motor_list[1], left_speed)
        
        # Правые моторы (M3_FR и M4_RR) - последние два в словаре
        self._set_motor_speed(motor_list[2], right_speed)
        self._set_motor_speed(motor_list[3], right_speed)
    
    def _set_direction(self, left_forward, right_forward):
        """Установка направления движения"""
        motor_list = list(MOTORS.keys())
        
        # Получаем пины для каждого мотора
        m1_pins = MOTORS[motor_list[0]]  # M1_RL
        m2_pins = MOTORS[motor_list[1]]  # M2_FL
        m3_pins = MOTORS[motor_list[2]]  # M3_FR
        m4_pins = MOTORS[motor_list[3]]  # M4_RR
        
        # Левые моторы (M1 и M2)
        if left_forward:
            self.gpio.output(m1_pins['pin1'], 1)
            self.gpio.output(m1_pins['pin2'], 0)
            self.gpio.output(m2_pins['pin1'], 0)
            self.gpio.output(m2_pins['pin2'], 1)
        else:
            self.gpio.output(m1_pins['pin1'], 0)
            self.gpio.output(m1_pins['pin2'], 1)
            self.gpio.output(m2_pins['pin1'], 1)
            self.gpio.output(m2_pins['pin2'], 0)
        
        # Правые моторы (M3 и M4)
        if right_forward:
            self.gpio.output(m3_pins['pin1'], 1)
            self.gpio.output(m3_pins['pin2'], 0)
            self.gpio.output(m4_pins['pin1'], 0)
            self.gpio.output(m4_pins['pin2'], 1)
        else:
            self.gpio.output(m3_pins['pin1'], 0)
            self.gpio.output(m3_pins['pin2'], 1)
            self.gpio.output(m4_pins['pin1'], 1)
            self.gpio.output(m4_pins['pin2'], 0)
    
    def soft_start_motor(self, motor_name, target_speed=75, steps=10):
        """Плавный запуск отдельного мотора"""
        if motor_name not in self.pwm_objects:
            logger.error(f"[Motor] Мотор {motor_name} не найден")
            return
        
        current_speed = 0
        step_size = target_speed / steps
        step_delay = SOFT_START_TIME / steps
        
        for i in range(steps + 1):
            speed = int(current_speed + i * step_size)
            self.pwm_objects[motor_name].ChangeDutyCycle(speed)
            time.sleep(step_delay)
        
        logger.info(f"[Motor] {motor_name} плавно разогнан до {target_speed}%")
    
    def soft_stop_motor(self, motor_name, steps=10):
        """Плавная остановка отдельного мотора"""
        if motor_name not in self.pwm_objects:
            logger.error(f"[Motor] Мотор {motor_name} не найден")
            return
        
        current_speed = self.default_speed
        step_size = current_speed / steps
        step_delay = SOFT_START_TIME / steps
        
        for i in range(steps + 1):
            speed = int(current_speed - i * step_size)
            if speed < 0:
                speed = 0
            self.pwm_objects[motor_name].ChangeDutyCycle(speed)
            time.sleep(step_delay)
        
        logger.info(f"[Motor] {motor_name} плавно остановлен")
    
    def stop(self):
        """Плавная остановка всех моторов"""
        print("🛑 ПЛАВНЫЙ СТОП")
        logger.info("[Motor] Плавная остановка всех моторов...")
        
        # Плавное снижение скорости
        for speed in range(self.default_speed, -1, -5):
            for pwm in self.pwm_objects.values():
                pwm.ChangeDutyCycle(speed)
            time.sleep(SOFT_START_TIME / 10)
        
        # Выключение всех пинов направления
        for motor_name, pins in MOTORS.items():
            self.gpio.output(pins['pin1'], 0)
            self.gpio.output(pins['pin2'], 0)
        
        print("✅ Полная остановка")
    
    def forward(self):
        """Движение вперёд с плавным стартом"""
        print("⬆️  ВПЕРЁД")
        self._set_direction(True, True)
        
        # Плавный запуск
        for speed in range(0, self.default_speed + 1, 5):
            self._set_motors(speed, speed)
            time.sleep(SOFT_START_TIME / 15)
    
    def backward(self):
        """Движение назад с плавным стартом"""
        print("⬇️  НАЗАД")
        self._set_direction(False, False)
        
        # Плавный запуск
        for speed in range(0, self.default_speed + 1, 5):
            self._set_motors(speed, speed)
            time.sleep(SOFT_START_TIME / 15)
    
    def left(self):
        """Поворот налево (левые колёса назад, правые вперёд)"""
        print("⬅️  ВЛЕВО")
        self._set_direction(False, True)
        self._set_motors(self.default_speed, self.default_speed)
    
    def right(self):
        """Поворот направо (левые вперёд, правые назад)"""
        print("➡️  ВПРАВО")
        self._set_direction(True, False)
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
        """Очистка ресурсов с плавной остановкой"""
        logger.info("[Motor] Начало очистки ресурсов...")
        self.stop()  # Уже плавный
        
        # Остановка всех PWM
        for motor_name, pwm in self.pwm_objects.items():
            pwm.stop()
            logger.debug(f"[Motor] PWM {motor_name} остановлен")
        
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