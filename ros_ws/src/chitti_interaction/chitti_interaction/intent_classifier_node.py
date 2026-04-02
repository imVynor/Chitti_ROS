# Intent Classifier Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class IntentClassifierNode(Node):
    
    def __init__(self):
        super().__init__('intent_classifier_node')
        
        # Subscribers
        self.text_input_sub = self.create_subscription(
            String, '/voice/text_input',
            self.text_input_callback, 10)
        
        # Publishers
        self.intent_pub = self.create_publisher(String, '/intent', 10)
        
        self.get_logger().info('Intent Classifier Node initialized')
    
    def text_input_callback(self, msg):
        """Classify user intent from text"""
        text = msg.data.lower()
        intent = self.classify_intent(text)
        
        intent_msg = String()
        intent_msg.data = intent
        self.intent_pub.publish(intent_msg)
        
        self.get_logger().info(f'Classified intent: {intent}')
    
    def classify_intent(self, text: str) -> str:
        """Classify intent based on keywords"""
        # Navigation intents
        navigation_keywords = ['take', 'go', 'move', 'navigate', 'lead', 'bring']
        question_keywords = ['tell', 'what', 'where', 'how', 'when', 'why', 'about']
        tour_keywords = ['tour', 'show', 'visit', 'guide']
        
        if any(word in text for word in navigation_keywords):
            return 'NAVIGATION'
        elif any(word in text for word in question_keywords):
            return 'QUESTION'
        elif any(word in text for word in tour_keywords):
            return 'TOUR'
        else:
            return 'OTHER'


def main(args=None):
    rclpy.init(args=args)
    node = IntentClassifierNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
