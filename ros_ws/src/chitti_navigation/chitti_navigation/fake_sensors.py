import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from sensor_msgs.msg import NavSatFix
from sensor_msgs.msg import NavSatStatus
from nav_msgs.msg import Path
import math

class FakeImuOnly(Node):
    def __init__(self):
        super().__init__('fake_sensors') # Kept the same node name so your setup.py still works
        
        # Publish to 'imu/data' to match your project doc specifications
        self.imu_pub = self.create_publisher(Imu, 'imu/data', 10) 
        self.fix_pub = self.create_publisher(NavSatFix, '/fix', 10)
        self.path_sub = self.create_subscription(Path, '/global_path', self.path_callback, 10)

        # Use a stable campus center fix as fallback localization in simulation.
        self.default_lat = 23.213911122480645
        self.default_lon = 72.68500570339303
        self.datum_lat = 23.2164
        self.datum_lon = 72.6836
        self.path_points = []
        self.path_index = 0
        self.timer = self.create_timer(0.1, self.timer_callback) # 10 Hz
        self.get_logger().info("Publishing fake IMU + GPS fix data at 10Hz...")

    def path_callback(self, msg):
        points = []
        for pose in msg.poses:
            x = float(pose.pose.position.x)
            y = float(pose.pose.position.y)
            lat = self.datum_lat + (y / 111320.0)
            lon = self.datum_lon + (x / (111320.0 * math.cos(math.radians(self.datum_lat))))
            points.append((lat, lon))

        if points:
            self.path_points = points
            self.path_index = 0
            self.get_logger().info(f'Received /global_path for fake movement with {len(points)} points')

    def timer_callback(self):
        now = self.get_clock().now().to_msg()
        
        # Publish Fake IMU
        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'imu_link'
        imu_msg.orientation.w = 1.0 # Neutral orientation
        self.imu_pub.publish(imu_msg)

        fix_msg = NavSatFix()
        fix_msg.header.stamp = now
        fix_msg.header.frame_id = 'gps_link'
        fix_msg.status.status = NavSatStatus.STATUS_FIX
        fix_msg.status.service = NavSatStatus.SERVICE_GPS
        if self.path_points:
            lat, lon = self.path_points[self.path_index]
            if self.path_index < len(self.path_points) - 1:
                self.path_index += 1
        else:
            lat, lon = self.default_lat, self.default_lon

        fix_msg.latitude = float(lat)
        fix_msg.longitude = float(lon)
        fix_msg.altitude = 0.0
        fix_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self.fix_pub.publish(fix_msg)

def main(args=None):
    rclpy.init(args=args)
    node = FakeImuOnly()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()