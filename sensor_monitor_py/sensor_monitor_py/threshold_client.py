# CLI 입력을 검사한 뒤 임계값 변경을 한 번 요청합니다.
import sys

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from mysensor_interfaces.srv import SetThreshold


class ThresholdClient(Node):
    def __init__(self):
        super().__init__('threshold_client')
        self.client = self.create_client(SetThreshold, '/set_threshold')

    def parse_threshold(self, arguments):
        if len(arguments) != 1:
            self.get_logger().warning('Exactly one threshold value is required.')
            return None
        try:
            return float(arguments[0])
        except ValueError:
            self.get_logger().warning('Threshold must be a number.')
            return None

    def send_request(self, threshold):
        request = SetThreshold.Request()
        request.new_threshold = threshold
        return self.client.call_async(request)

    def log_response(self, response, threshold):
        if response.success:
            self.get_logger().info(f'Threshold changed to {threshold:.2f}')
        else:
            self.get_logger().warning(f'Invalid threshold: {threshold:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = ThresholdClient()
    try:
        # main(args=...)의 인자는 실행 파일명을 포함하지 않습니다.
        argv = sys.argv if args is None else ['threshold_client', *args]
        arguments = remove_ros_args(args=argv)[1:]
        threshold = node.parse_threshold(arguments)
        if threshold is None:
            return

        # NaN, 무한대, 범위 밖 숫자의 최종 허용 여부는 서버가 판단합니다.
        while not node.client.wait_for_service(timeout_sec=1.0):
            if not rclpy.ok():
                return

        future = node.send_request(threshold)
        rclpy.spin_until_future_complete(node, future)
        if future.done() and not future.cancelled():
            node.log_response(future.result(), threshold)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
