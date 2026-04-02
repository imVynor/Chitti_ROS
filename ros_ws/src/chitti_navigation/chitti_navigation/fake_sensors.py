import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus


class FakeSensorPublisher(Node):

    def __init__(self):
        super().__init__('fake_sensor_publisher')
        self.gps_pub = self.create_publisher(NavSatFix, '/fix', 10)
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.timer = self.create_timer(0.1, self.publish_sensors)
        self.get_logger().info('Fake sensor publisher started')

    def publish_sensors(self):
        now = self.get_clock().now().to_msg()

        gps_msg = NavSatFix()
        gps_msg.header.stamp = now
        # Spawn the robot physically at the Hostels
        gps_msg.latitude = 23.2119
        gps_msg.longitude = 72.6844
        gps_msg.altitude = 81.0
        gps_msg.position_covariance = [
            6.25, 0.0, 0.0,
            0.0, 6.25, 0.0,
            0.0, 0.0, 6.25,
        ]
        gps_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self.gps_pub.publish(gps_msg)

        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'base_link'
        imu_msg.orientation.x = 0.0
        imu_msg.orientation.y = 0.0
        # Set yaw to +90 deg (North) so it faces the library path again!
        imu_msg.orientation.z = 0.707
        imu_msg.orientation.w = 0.707
        imu_msg.angular_velocity.x = 0.0
        imu_msg.angular_velocity.y = 0.0
        imu_msg.angular_velocity.z = 0.0
        imu_msg.linear_acceleration.x = 0.0
        imu_msg.linear_acceleration.y = 0.0
        imu_msg.linear_acceleration.z = 9.81
        imu_msg.orientation_covariance = [
            0.01, 0.0, 0.0,
            0.0, 0.01, 0.0,
            0.0, 0.0, 0.01,
        ]
        imu_msg.angular_velocity_covariance = [
            0.01, 0.0, 0.0,
            0.0, 0.01, 0.0,
            0.0, 0.0, 0.01,
        ]
        imu_msg.linear_acceleration_covariance = [
            0.1, 0.0, 0.0,
            0.0, 0.1, 0.0,
            0.0, 0.0, 0.1,
        ]
        self.imu_pub.publish(imu_msg)


def main(args=None):
    rclpy.init(args=args)
    node = FakeSensorPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
