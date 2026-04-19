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
            'library':        'This is the Central Library at IIT Gandhinagar, available 24/7 with study areas and digital resources.',
            'jibaben':        'This is Jibaben, one of the key buildings on campus.',
            'jasubhai':       'This is the Jasubhai Auditorium, the main venue for events and presentations.',
            'duven':          'This is Duven Hostel, providing residential accommodation for students.',
            'sports_complex': 'This is the Sports Complex, equipped with courts and facilities for various sports.',
            'guest_house':    'This is the Guest House, for visiting faculty and guests of the institute.',
            'jaiswal_mess':   'This is the Jaiswal Mess, one of the main student dining facilities.',
            'new_pc':         'This is the New PC area on campus.',
            'rangmanch':      'This is Rangmanch, the cultural activity centre of IIT Gandhinagar.',
            'gate_1':         'This is Gate 1, the main entrance to the IIT Gandhinagar campus.',
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
