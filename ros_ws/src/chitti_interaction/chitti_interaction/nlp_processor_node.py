# NLP Processor Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class NLPProcessorNode(Node):
    
    def __init__(self):
        super().__init__('nlp_processor_node')
        
        # Subscribers
        self.voice_input_sub = self.create_subscription(
            String, '/voice/text_input',
            self.voice_input_callback, 10)
        
        # Publishers
        self.intent_pub = self.create_publisher(String, '/intent', 10)
        
        self.get_logger().info('NLP Processor Node initialized')
    
    def voice_input_callback(self, msg):
        """Process voice input text"""
        text = msg.data.lower()
        self.get_logger().info(f'Processing text: {text}')
        
        # Simple keyword matching for intents
        if any(word in text for word in ['take', 'go', 'move', 'navigate']):
            intent = 'NAVIGATION'
        elif any(word in text for word in ['tell', 'what', 'where', 'how', 'when', 'why']):
            intent = 'QUESTION'
        elif any(word in text for word in ['tour', 'show', 'visit']):
            intent = 'TOUR'
        else:
            intent = 'OTHER'
        
        # Publish intent
        intent_msg = String()
        intent_msg.data = intent
        self.intent_pub.publish(intent_msg)


def main(args=None):
    rclpy.init(args=args)
    node = NLPProcessorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
