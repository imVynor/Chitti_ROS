# Response Generator Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ResponseGeneratorNode(Node):
    
    def __init__(self):
        super().__init__('response_generator_node')
        
        # Subscribers
        self.intent_sub = self.create_subscription(
            String, '/intent',
            self.intent_callback, 10)
        
        self.voice_input_sub = self.create_subscription(
            String, '/voice/text_input',
            self.voice_input_callback, 10)
        
        # Publishers
        self.response_pub = self.create_publisher(String, '/robot/response_text', 10)
        
        # Store last recognized intent
        self.last_intent = 'OTHER'
        self.last_voice_input = ''
        
        self.get_logger().info('Response Generator Node initialized')
    
    def intent_callback(self, msg):
        """Handle intent messages"""
        self.last_intent = msg.data
    
    def voice_input_callback(self, msg):
        """Generate response for voice input"""
        self.last_voice_input = msg.data
        response = self.generate_response(self.last_intent, msg.data)
        
        response_msg = String()
        response_msg.data = response
        self.response_pub.publish(response_msg)
        
        self.get_logger().info(f'Generated response: {response}')
    
    def generate_response(self, intent: str, voice_input: str) -> str:
        """Generate contextual response"""
        responses = {
            'NAVIGATION': 'Sure, I will navigate there for you.',
            'QUESTION': 'That is a great question. Let me provide you with information.',
            'TOUR': 'Excellent choice! I will conduct a guided tour for you.',
            'OTHER': 'I understand. How can I help you further?'
        }
        
        return responses.get(intent, responses['OTHER'])


def main(args=None):
    rclpy.init(args=args)
    node = ResponseGeneratorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
