import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix
from nav_msgs.msg import Odometry
import math

class FakeSensorPublisher(Node):

    def __init__(self):
        super().__init__('fake_sensor_publisher')
        self.gps_pub = self.create_publisher(NavSatFix, '/fix', 10)
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        
        # Subscribe to wheel odometry to fake a moving GPS!
        self.odom_sub = self.create_subscription(Odometry, '/diff_drive_controller/odom', self.odom_callback, 10)
        self.odom_x = 0.0
        self.odom_y = 0.0
        self.odom_yaw_q = [0.0, 0.0, 0.0, 1.0]
        
        self.timer = self.create_timer(0.1, self.publish_sensors)
        self.get_logger().info('Moving Fake sensor publisher started')

    def odom_callback(self, msg):
        # Read exactly how far the wheels drove mathematically
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y
        self.odom_yaw_q = [
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w
        ]

    def publish_sensors(self):
        now = self.get_clock().now().to_msg()

        gps_msg = NavSatFix()
        gps_msg.header.stamp = now
        gps_msg.header.frame_id = 'gps_link'
        
        # Convert wheel movement (meters) into fake GPS coordinates
        # 1 degree of latitude is ~111,111 meters
        # 1 degree of longitude at 23.2N is ~102,150 meters
        gps_msg.latitude = 23.2119 + (self.odom_x / 111111.0)
        gps_msg.longitude = 72.6844 + (self.odom_y / 102150.0)
        gps_msg.altitude = 81.0
        gps_msg.position_covariance = [6.25, 0.0, 0.0, 0.0, 6.25, 0.0, 0.0, 0.0, 6.25]
        gps_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self.gps_pub.publish(gps_msg)

        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'base_link'
        imu_msg.orientation.x = self.odom_yaw_q[0]
        imu_msg.orientation.y = self.odom_yaw_q[1]
        imu_msg.orientation.z = self.odom_yaw_q[2]
        imu_msg.orientation.w = self.odom_yaw_q[3]
        imu_msg.angular_velocity.x = 0.0
        imu_msg.angular_velocity.y = 0.0
        imu_msg.angular_velocity.z = 0.0
        imu_msg.linear_acceleration.x = 0.0
        imu_msg.linear_acceleration.y = 0.0
        imu_msg.linear_acceleration.z = 9.81
        imu_msg.orientation_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        imu_msg.angular_velocity_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        imu_msg.linear_acceleration_covariance = [0.1, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1]
        self.imu_pub.publish(imu_msg)

def main(args=None):
    rclpy.init(args=args)
    node = FakeSensorPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
