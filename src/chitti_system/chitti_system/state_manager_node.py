# State Manager Node
from enum import Enum
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty
from chitti_msgs.msg import LocationRequest, RobotState, ScreenState


class RobotStateEnum(Enum):
    IDLE = "idle"
    UI_INTERACTION = "ui_interaction"
    DESTINATION_SELECTED = "destination_selected"
    QR_DISPLAYED = "qr_displayed"
    VOICE_PROCESSING = "voice_processing"
    NAVIGATING = "navigating"
    TOUR_ACTIVE = "tour_active"
    SPEAKING = "speaking"
    CHARGING = "charging"
    ERROR = "error"


class StateManagerNode(Node):
    
    def __init__(self):
        super().__init__('state_manager_node')
        
        self.current_state = RobotStateEnum.IDLE
        
        # Publishers
        self.state_pub = self.create_publisher(RobotState, '/robot_state', 10)
        
        # Subscribers
        self.destination_sub = self.create_subscription(
            LocationRequest, '/ui/destination_selected',
            self.destination_callback, 10)
        
        self.screen_state_sub = self.create_subscription(
            ScreenState, '/ui/screen_state',
            self.screen_state_callback, 10)
        
        # Timer for periodic state publishing
        self.timer = self.create_timer(1.0, self.publish_state)
        
        self.get_logger().info('State Manager Node initialized')
    
    def destination_callback(self, msg):
        """Handle destination selection"""
        self.transition_to_state(RobotStateEnum.DESTINATION_SELECTED)
    
    def screen_state_callback(self, msg):
        """Handle screen state changes"""
        if msg.current_screen == 'qr_display':
            self.transition_to_state(RobotStateEnum.QR_DISPLAYED)
        elif msg.current_screen == 'navigation_active':
            self.transition_to_state(RobotStateEnum.NAVIGATING)
    
    def transition_to_state(self, new_state: RobotStateEnum):
        """Transition to a new state"""
        self.get_logger().info(f'State transition: {self.current_state.value} -> {new_state.value}')
        self.current_state = new_state
    
    def publish_state(self):
        """Publish current robot state"""
        msg = RobotState()
        msg.state = self.current_state.value
        msg.ui_state = "unknown"
        msg.timestamp = float(self.get_clock().now().nanoseconds) / 1e9
        
        self.state_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = StateManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
