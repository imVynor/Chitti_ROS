# Voice Input Server Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from chitti_msgs.srv import CreateSession, CloseSession


class VoiceInputServerNode(Node):
    
    def __init__(self):
        super().__init__('voice_input_server_node')
        
        # Publishers
        self.voice_input_pub = self.create_publisher(String, '/voice/text_input', 10)
        
        # Subscribers
        self.web_input_sub = self.create_subscription(
            String, '/web/voice_input',
            self.web_voice_input_callback, 10)
        
        # Service clients
        self.create_session_cli = self.create_client(CreateSession, '/session/create_voice_session')
        self.close_session_cli = self.create_client(CloseSession, '/session/close_session')
        
        self.get_logger().info('Voice Input Server Node initialized')
    
    def web_voice_input_callback(self, msg):
        """Handle voice input from web interface"""
        # Parse session_id:text format
        parts = msg.data.split(':', 1)
        if len(parts) == 2:
            session_id, voice_text = parts
            self.get_logger().info(f'Voice input from session {session_id}: {voice_text}')
            
            # Publish to NLP processor
            output_msg = String()
            output_msg.data = voice_text
            self.voice_input_pub.publish(output_msg)


def main(args=None):
    rclpy.init(args=args)
    node = VoiceInputServerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
