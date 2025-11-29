# логика движения
# если впереди препятствие — останавливается и разворачивается;
# если свободно — едет вперёд.


from robot.sensors import DistanceSensor
from robot.actuators import Motor

class Navigator:
    def __init__(self, sensor: DistanceSensor, left_motor: Motor, right_motor: Motor):
        self.sensor = sensor
        self.left_motor = left_motor
        self.right_motor = right_motor

    def move_forward(self, speed: int = 50):
        self.left_motor.set_speed(speed)
        self.right_motor.set_speed(speed)

    def stop(self):
        self.left_motor.set_speed(0)
        self.right_motor.set_speed(0)

    def avoid_obstacle(self):
        if self.sensor.is_obstacle():
            print("Препятствие! Останавливаюсь.")
            self.stop()
            time.sleep(1)
            print("Разворачиваюсь...")
            # Пример разворота
            self.left_motor.set_speed(-40)
            self.right_motor.set_speed(40)
            time.sleep(1.5)
            self.stop()
        else:
            self.move_forward(40)