import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix
from tf2_msgs.msg import TFMessage

class Checker(Node):
    def __init__(self):
        super().__init__('checker')
        self.create_subscription(Odometry, '/odometry/filtered', self.odom_cb, 10)
        self.create_subscription(NavSatFix, '/gps/filtered', self.gps_cb, 10)
        self.create_subscription(TFMessage, '/tf', self.tf_cb, 10)
        self.get_logger().info('Checking topics...')

    def odom_cb(self, msg):
        pos = msg.pose.pose.position
        print(f"ODOM: x={pos.x:.2f}, y={pos.y:.2f}, frame={msg.header.frame_id}")

    def gps_cb(self, msg):
        print(f"GPS: lat={msg.latitude:.6f}, lon={msg.longitude:.6f}")

    def tf_cb(self, msg):
        for transform in msg.transforms:
            if transform.header.frame_id == 'map' and transform.child_frame_id == 'odom':
                t = transform.transform.translation
                print(f"TF map->odom: x={t.x:.2f}, y={t.y:.2f}")

def main():
    rclpy.init()
    node = Checker()
    # Spin for 10 seconds to catch messages
    import time
    start = time.time()
    while time.time() - start < 10:
        rclpy.spin_once(node, timeout_sec=0.1)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
