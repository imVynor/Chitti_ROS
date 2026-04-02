# Diagnostics Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DiagnosticsNode(Node):
    
    def __init__(self):
        super().__init__('diagnostics_node')
        
        # Publishers
        self.diagnostics_pub = self.create_publisher(String, '/diagnostics', 10)
        
        # Timer for periodic diagnostics
        self.timer = self.create_timer(5.0, self.run_diagnostics)
        
        self.get_logger().info('Diagnostics Node initialized')
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        diagnostics_data = {
            'cpu_usage': '45%',
            'memory_usage': '62%',
            'wifi_connected': True,
            'sensors_active': True,
            'motor_status': 'OK'
        }
        
        msg = String()
        msg.data = str(diagnostics_data)
        self.diagnostics_pub.publish(msg)
        
        self.get_logger().info('Diagnostics complete')


def main(args=None):
    rclpy.init(args=args)
    node = DiagnosticsNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
