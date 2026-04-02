# UI State Manager Node
from enum import Enum
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty
from chitti_msgs.msg import LocationRequest, ScreenState


class UIState(Enum):
    HOME = "home"
    LOCATION_SELECTION = "location_selection"
    VOICE_INPUT = "voice_input"
    NAVIGATION_ACTIVE = "navigation_active"
    TOUR_MODE = "tour_mode"
    SETTINGS = "settings"
    ACCESSIBILITY = "accessibility"
    QR_DISPLAY = "qr_display"
    ERROR = "error"


class UIStateManagerNode(Node):
    
    def __init__(self):
        super().__init__('ui_state_manager_node')
        
        self.current_state = UIState.HOME
        
        # Publishers
        self.screen_state_pub = self.create_publisher(ScreenState, '/ui/screen_state', 10)
        
        # Subscribers
        self.destination_sub = self.create_subscription(
            LocationRequest, '/ui/destination_selected',
            self.destination_callback, 10)
        
        self.mic_button_sub = self.create_subscription(
            Empty, '/ui/mic_button_pressed',
            self.mic_button_callback, 10)
        
        # Timer for periodic state publishing
        self.timer = self.create_timer(1.0, self.publish_screen_state)
        
        self.get_logger().info('UI State Manager Node initialized')
    
    def transition_to_state(self, new_state: UIState):
        """Handle UI state transitions with validation"""
        valid_transitions = {
            UIState.HOME: [UIState.LOCATION_SELECTION, UIState.SETTINGS, UIState.ACCESSIBILITY, UIState.VOICE_INPUT],
            UIState.LOCATION_SELECTION: [UIState.HOME, UIState.NAVIGATION_ACTIVE],
            UIState.VOICE_INPUT: [UIState.HOME, UIState.QR_DISPLAY],
            UIState.QR_DISPLAY: [UIState.HOME, UIState.VOICE_INPUT],
            UIState.NAVIGATION_ACTIVE: [UIState.HOME, UIState.TOUR_MODE],
            UIState.TOUR_MODE: [UIState.HOME, UIState.NAVIGATION_ACTIVE],
            UIState.SETTINGS: [UIState.HOME],
            UIState.ACCESSIBILITY: [UIState.HOME],
            UIState.ERROR: [UIState.HOME],
        }
        
        if new_state in valid_transitions.get(self.current_state, []):
            self.get_logger().info(f'UI State: {self.current_state.value} -> {new_state.value}')
            self.current_state = new_state
            self.publish_screen_state()
            return True
        return False
    
    def destination_callback(self, msg):
        """Handle destination selection"""
        self.transition_to_state(UIState.NAVIGATION_ACTIVE)
    
    def mic_button_callback(self, msg):
        """Handle mic button press"""
        self.transition_to_state(UIState.QR_DISPLAY)
    
    def publish_screen_state(self):
        """Publish current screen state"""
        msg = ScreenState()
        msg.current_screen = self.current_state.value
        msg.available_options = ['academic_block', 'library', 'cafeteria', 'hostels', 'admin', 'auditorium']
        msg.mic_button_enabled = self.current_state in [UIState.HOME, UIState.LOCATION_SELECTION]
        msg.emergency_button_enabled = True
        msg.screen_brightness = 80.0
        
        self.screen_state_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = UIStateManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
