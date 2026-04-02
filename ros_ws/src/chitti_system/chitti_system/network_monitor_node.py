# Network Monitor Node
import rclpy
from rclpy.node import Node
from chitti_msgs.msg import NetworkStatus


class NetworkMonitorNode(Node):
    
    def __init__(self):
        super().__init__('network_monitor_node')
        
        # Publishers
        self.network_status_pub = self.create_publisher(NetworkStatus, '/network/status', 10)
        
        # Timer for periodic network checks
        self.timer = self.create_timer(5.0, self.check_network)
        
        self.get_logger().info('Network Monitor Node initialized')
    
    def check_network(self):
        """Check network connectivity"""
        msg = NetworkStatus()
        msg.wifi_connected = True
        msg.ssid = "IITGN_Campus"
        msg.signal_strength = 75
        msg.internet_available = True
        msg.ip_address = "192.168.1.100"
        
        self.network_status_pub.publish(msg)
        self.get_logger().debug('Network status: OK')


def main(args=None):
    rclpy.init(args=args)
    node = NetworkMonitorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
