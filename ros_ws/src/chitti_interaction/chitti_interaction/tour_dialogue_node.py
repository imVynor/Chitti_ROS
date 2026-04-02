# Tour Dialogue Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from chitti_msgs.msg import TourStatus


class TourDialogueNode(Node):
    
    def __init__(self):
        super().__init__('tour_dialogue_node')
        
        # Tour scripts
        self.tour_scripts = {
            'academic_block': 'This is the IIT Gandhinagar Academic Block. It houses classrooms and faculty offices.',
            'library': 'This is the Central Library, available 24/7 with study areas and digital resources.',
            'cafeteria': 'Welcome to the Main Cafeteria with multiple food options for students.',
            'hostels': 'These are the Student Hostels providing accommodation for students.',
            'admin': 'This is the Administration Block with administrative offices.',
            'auditorium': 'This is the Main Auditorium used for events and presentations.',
        }
        
        # Subscribers
        self.tour_status_sub = self.create_subscription(
            TourStatus, '/tour/status',
            self.tour_status_callback, 10)
        
        # Publishers
        self.dialogue_pub = self.create_publisher(String, '/robot/response_text', 10)
        
        self.get_logger().info('Tour Dialogue Node initialized')
    
    def tour_status_callback(self, msg):
        """Generate tour dialogue for current location"""
        location_description = self.tour_scripts.get(
            msg.current_location_description.lower(),
            f'You have reached {msg.current_location_description}.'
        )
        
        dialogue = String()
        dialogue.data = location_description
        self.dialogue_pub.publish(dialogue)
        
        self.get_logger().info(f'Tour dialogue: {location_description}')


def main(args=None):
    rclpy.init(args=args)
    node = TourDialogueNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
