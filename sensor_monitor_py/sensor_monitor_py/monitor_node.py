# /sensor_data 토픽을 구독하고, 
# threshold와 온도를 비교해서 INFO / WARN을 출력함.
# 동시에 /set_threshold 서비스 서버도 운영 -> 요청이 오면 자기 내부 threshold 값 변경
import math
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from mysensor_interfaces.msg import MySensorMsg
from mysensor_interfaces.srv import SetThreshold

class MonitorNode(Node):
	def __init__(self):
		super().__init__('monitor_node')
		
		# 초기 threshold
		self.threshold = 30.0
		
		# /sensor_data 토픽 구독
		self.subscription = self.create_subscription(
			MySensorMsg,
			'/sensor_data',
			self.sensor_callback,
			10
		)

		# /set_threshold 서비스 서버 생성
		self.service = self.create_service(
			SetThreshold,
			'/set_threshold',
			self.threshold_callback
		)

	def sensor_callback(self, msg):
		# 출력할 문자열
		message = (
			f'id={msg.sensor_id}, '
			f'temp={msg.temp:.2f}, '
			f'humidity={msg.humidity:.2f}, '
			f'stamp={msg.stamp.sec}.{msg.stamp.nsec:09d}, '
			f'threshold={self.threshold:.2f}'
		)

		# 온도와 threshold 비교
		if msg.temp < self.threshold:
			self.get_logger().info(message)

		else :
			self.get_logger().warning(message)
	
	# /set_threshold 서비스 요청이 들어왔을 때 실행된다.
	def threshold_callback(self, request, response):
		new_threshold = request.new_threshold

		# 유한한 실수이고 -10 ~ 50 범위인지 검사
		if math.isfinite(new_threshold) and -10.0 <= new_threshold <= 50.0:
			self.threshold = new_threshold
			response.success = True
		else:
			response.success = False

		return response

	
def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
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
