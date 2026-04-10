import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

class FakeImuOnly(Node):
    def __init__(self):
        super().__init__('fake_sensors') # Kept the same node name so your setup.py still works
        
        # Publish to 'imu/data' to match your project doc specifications
        self.imu_pub = self.create_publisher(Imu, 'imu/data', 10) 
        self.timer = self.create_timer(0.1, self.timer_callback) # 10 Hz
        self.get_logger().info("Publishing ONLY fake IMU data at 10Hz...")

    def timer_callback(self):
        now = self.get_clock().now().to_msg()
        
        # Publish Fake IMU
        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'imu_link'
        imu_msg.orientation.w = 1.0 # Neutral orientation
        self.imu_pub.publish(imu_msg)

def main(args=None):
    rclpy.init(args=args)
    node = FakeImuOnly()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()