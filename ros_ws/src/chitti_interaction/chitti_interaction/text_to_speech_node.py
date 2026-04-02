# Text to Speech Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class TextToSpeechNode(Node):
    
    def __init__(self):
        super().__init__('text_to_speech_node')
        
        if PYTTSX3_AVAILABLE:
            self.tts_engine = pyttsx3.init()
            self.setup_tts_properties()
        else:
            self.tts_engine = None
            self.get_logger().warn('pyttsx3 not available')
        
        # Subscribers
        self.response_sub = self.create_subscription(
            String, '/robot/response_text',
            self.response_callback, 10)
        
        self.get_logger().info('Text to Speech Node initialized')
    
    def setup_tts_properties(self):
        """Configure TTS engine"""
        if not self.tts_engine:
            return
        
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)
    
    def response_callback(self, msg):
        """Speak the response"""
        if self.tts_engine:
            try:
                self.get_logger().info(f'Speaking: {msg.data}')
                self.tts_engine.say(msg.data)
                self.tts_engine.runAndWait()
            except Exception as e:
                self.get_logger().error(f'TTS error: {str(e)}')


def main(args=None):
    rclpy.init(args=args)
    node = TextToSpeechNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
