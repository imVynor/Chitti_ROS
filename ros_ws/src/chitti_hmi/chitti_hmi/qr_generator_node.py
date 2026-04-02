# QR Code Generator Node
import qrcode
import io
import base64
import uuid
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from chitti_msgs.msg import QRCode
from chitti_msgs.srv import CreateSession


class QRGeneratorNode(Node):
    
    def __init__(self):
        super().__init__('qr_generator_node')
        
        # Service server
        self.srv = self.create_service(
            CreateSession, '/session/create_voice_session',
            self.create_qr_session_callback)
        
        # Publisher
        self.qr_pub = self.create_publisher(QRCode, '/voice/qr_code', 10)
        
        # Parameters
        self.declare_parameter('base_url', 'http://192.168.1.100:5000')
        self.base_url = self.get_parameter('base_url').value
        
        self.get_logger().info('QR Generator Node initialized')
    
    def create_qr_session_callback(self, request, response):
        """Generate QR code for voice input session"""
        try:
            session_id = str(uuid.uuid4())
            voice_url = f"{self.base_url}/voice/{session_id}"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(voice_url)
            qr.make(fit=True)
            
            # Convert to base64
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Create and publish QR message
            qr_msg = QRCode()
            qr_msg.session_id = session_id
            qr_msg.qr_data = qr_base64
            qr_msg.web_url = voice_url
            qr_msg.expiry_time = self.get_clock().now().to_msg()
            
            self.qr_pub.publish(qr_msg)
            
            # Service response
            response.session_id = session_id
            response.qr_code_url = voice_url
            response.success = True
            
            self.get_logger().info(f'QR code generated for session: {session_id}')
            return response
            
        except Exception as e:
            self.get_logger().error(f'Error generating QR code: {str(e)}')
            response.success = False
            return response


def main(args=None):
    rclpy.init(args=args)
    node = QRGeneratorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
