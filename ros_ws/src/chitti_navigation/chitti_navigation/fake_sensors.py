import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from sensor_msgs.msg import NavSatFix
from sensor_msgs.msg import NavSatStatus
from nav_msgs.msg import Path
from nav_msgs.msg import Odometry
import pyproj
import math

class FakeImuOnly(Node):
    def __init__(self):
        super().__init__('fake_sensors')
        
        self.imu_pub = self.create_publisher(Imu, 'imu/data', 10) 
        self.fix_pub = self.create_publisher(NavSatFix, '/fix', 10)
        self.odom_sub = self.create_subscription(Odometry, '/diff_drive_controller/odom', self.odom_callback, 10)

        self.datum_lat = 23.210142
        self.datum_lon = 72.688199

        # Create UTM transformers (same logic as OSRM node)
        self.transformer_to_utm = pyproj.Transformer.from_crs("epsg:4326", "epsg:32643", always_xy=True)
        self.transformer_to_latlon = pyproj.Transformer.from_crs("epsg:32643", "epsg:4326", always_xy=True)

        # Pre-calculate UTM coordinates of the datum
        self.datum_x, self.datum_y = self.transformer_to_utm.transform(self.datum_lon, self.datum_lat)

        self.current_lat = self.datum_lat
        self.current_lon = self.datum_lon
        self.current_orientation = None

        self.timer = self.create_timer(0.1, self.timer_callback) # 10 Hz
        self.get_logger().info("Publishing fake IMU + GPS fix data synced to Gazebo Odometry at 10Hz...")

    def odom_callback(self, msg):
        # Convert Gazebo X/Y into simulated geographical coordinates using UTM projection
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        # Add Gazebo offset to UTM datum
        utm_x = self.datum_x + x
        utm_y = self.datum_y + y

        # Convert back to lat/lon
        lon, lat = self.transformer_to_latlon.transform(utm_x, utm_y)
        
        self.current_lat = lat
        self.current_lon = lon
        self.current_orientation = msg.pose.pose.orientation

    def timer_callback(self):
        now = self.get_clock().now().to_msg()
        
        # Publish Fake IMU
        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'imu_link'
        if self.current_orientation:
            imu_msg.orientation = self.current_orientation
        else:
            imu_msg.orientation.w = 1.0 # Neutral orientation
        self.imu_pub.publish(imu_msg)

        # Publish Fake GPS
        fix_msg = NavSatFix()
        fix_msg.header.stamp = now
        fix_msg.header.frame_id = 'gps_link'
        fix_msg.status.status = NavSatStatus.STATUS_FIX
        fix_msg.status.service = NavSatStatus.SERVICE_GPS
        
        fix_msg.latitude = float(self.current_lat)
        fix_msg.longitude = float(self.current_lon)
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