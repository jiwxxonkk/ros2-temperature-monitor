# /sensor_data를 monitor_node에 publish 해주는 파일
import random
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from mysensor_interfaces.msg import MySensorMsg
from mysensor_interfaces.msg import MyTime

class TemperaturePublisher(Node):
	def __init__(self):
		super().__init__('temperature_publisher')
		
		# /sensor_data 토픽 publisher 생성
		self.publisher_ = self.create_publisher(
			MySensorMsg,
			'/sensor_data',
			10
		)

		# 노드 시작 시각 저장
		self.t0 = self.get_clock().now()

		# 실행 중 고정해서 사용할 센서 이름
		self.declare_parameter('sensor_id', 'sensor_01')
		self.sensor_id = self.get_parameter('sensor_id').value

		# 1초마다 timer_callback() 실행
		self.timer = self.create_timer(
			1.0,
			self.timer_callback
		)

	def timer_callback(self):
		# 1. 온도 난수 생성
		temperature = random.uniform(-10.0, 50.0)
		# 2. 습도 난수 생성
		humidity = random.uniform(10.0, 99.0)
		# 3. 현재 시간 - 시작 시간
		now = self.get_clock().now()
		dt = now - self.t0
		total_nanoseconds = dt.nanoseconds
		# 4. sec / nsec 계산
		sec = total_nanoseconds // 1_000_000_000
		nsec = total_nanoseconds % 1_000_000_000
		# 5. MySensorMsg 생성
		msg = MySensorMsg()
		msg.temp = temperature
		msg.humidity = humidity
		msg.sensor_id = self.sensor_id
		msg.stamp.sec = int(sec)
		msg.stamp.nsec = int(nsec)
		# 6. publish
		self.publisher_.publish(msg)
		
def main(args=None):
    rclpy.init(args=args)
    node = TemperaturePublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
