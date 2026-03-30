# Audio Output Manager Node
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from chitti_msgs.msg import AudioMode
from chitti_msgs.srv import SetAudioMode

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class AudioOutputManagerNode(Node):
    
    def __init__(self):
        super().__init__('audio_output_manager_node')
        
        # Initialize TTS engine if available
        if PYTTSX3_AVAILABLE:
            self.tts_engine = pyttsx3.init()
            self.setup_tts_properties()
        else:
            self.get_logger().warn('pyttsx3 not installed, TTS disabled')
            self.tts_engine = None
        
        # Audio mode state
        self.current_mode = "robot_speaker"
        self.current_volume = 0.7
        
        # Subscribers
        self.response_sub = self.create_subscription(
            String, '/robot/response_text',
            self.speak_response_callback, 10)
        
        self.mode_sub = self.create_subscription(
            AudioMode, '/audio/output_mode',
            self.audio_mode_callback, 10)
        
        # Services
        self.audio_mode_service = self.create_service(
            SetAudioMode, '/audio/set_output_mode',
            self.set_audio_mode_callback)
        
        self.get_logger().info('Audio Output Manager Node initialized')
    
    def setup_tts_properties(self):
        """Configure TTS engine"""
        if not self.tts_engine:
            return
        
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)
    
    def speak_response_callback(self, msg):
        """Handle text-to-speech output"""
        text = msg.data
        self.get_logger().info(f'Speaking: {text}')
        
        if self.tts_engine and self.current_mode in ["robot_speaker", "both"]:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                self.get_logger().error(f'TTS error: {str(e)}')
    
    def audio_mode_callback(self, msg):
        """Handle audio mode changes"""
        self.current_mode = msg.output_device
        self.current_volume = msg.volume
        self.get_logger().info(f'Audio mode changed to: {self.current_mode}')
    
    def set_audio_mode_callback(self, request, response):
        """Set audio output mode"""
        self.current_mode = request.mode
        self.current_volume = request.volume
        response.success = True
        response.current_mode = self.current_mode
        self.get_logger().info(f'Audio mode set to: {self.current_mode}')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = AudioOutputManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
