# Touchscreen Interface Node
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


class TouchscreenInterfaceNode(Node):
    
    def __init__(self):
        super().__init__('touchscreen_interface_node')
        self.current_state = UIState.HOME
        
        # Publishers
        self.destination_pub = self.create_publisher(
            LocationRequest, '/ui/destination_selected', 10)
        self.mic_button_pub = self.create_publisher(
            Empty, '/ui/mic_button_pressed', 10)
        self.screen_state_pub = self.create_publisher(
            ScreenState, '/ui/screen_state', 10)
        
        # Configuration
        self.declare_parameter('resolution', '800x480')
        self.declare_parameter('brightness', 80)
        
        # Timer for periodic updates
        self.timer = self.create_timer(0.5, self.update_screen_state)
        
        self.get_logger().info('Touchscreen Interface Node initialized')
    
    def update_screen_state(self):
        """Publish current screen state"""
        msg = ScreenState()
        msg.current_screen = self.current_state.value
        msg.available_options = ['library', 'jibaben', 'jasubhai', 'duven', 'sports_complex', 'guest_house', 'jaiswal_mess', 'new_pc', 'rangmanch', 'gate_1']
        msg.mic_button_enabled = True
        msg.emergency_button_enabled = True
        msg.screen_brightness = float(self.get_parameter('brightness').value)
        
        self.screen_state_pub.publish(msg)
    
    def simulate_destination_selection(self, location_id: str):
        """Simulate user selecting a destination"""
        msg = LocationRequest()
        msg.location_id = location_id
        msg.location_name = location_id.replace('_', ' ').title()
        msg.coordinates.x = 23.5937
        msg.coordinates.y = 72.6837
        msg.coordinates.z = 0.0
        msg.urgent = False
        msg.accessibility_requirements = ""
        
        self.destination_pub.publish(msg)
        self.current_state = UIState.NAVIGATION_ACTIVE
        self.get_logger().info(f'Destination selected: {location_id}')
    
    def simulate_mic_button_press(self):
        """Simulate user pressing mic button"""
        msg = Empty()
        self.mic_button_pub.publish(msg)
        self.current_state = UIState.QR_DISPLAY
        self.get_logger().info('Mic button pressed')


def main(args=None):
    rclpy.init(args=args)
    node = TouchscreenInterfaceNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
