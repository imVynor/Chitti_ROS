# Battery Monitor Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class BatteryMonitorNode(Node):
    
    def __init__(self):
        super().__init__('battery_monitor_node')
        
        self.battery_level = 100.0
        
        # Publishers
        self.battery_pub = self.create_publisher(Float32, '/battery/level', 10)
        
        # Timer for periodic updates (simulate battery drain)
        self.timer = self.create_timer(2.0, self.update_battery)
        
        self.get_logger().info('Battery Monitor Node initialized')
    
    def update_battery(self):
        """Update and publish battery level"""
        # Simulate slow battery drain
        self.battery_level = max(0.0, self.battery_level - 0.1)
        
        msg = Float32()
        msg.data = self.battery_level
        self.battery_pub.publish(msg)
        
        if self.battery_level < 20.0:
            self.get_logger().warn(f'Low battery: {self.battery_level}%')


def main(args=None):
    rclpy.init(args=args)
    node = BatteryMonitorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
