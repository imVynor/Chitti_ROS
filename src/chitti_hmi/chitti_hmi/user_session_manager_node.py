# User Session Manager Node
import uuid
import rclpy
from rclpy.node import Node
from chitti_msgs.srv import CreateSession, CloseSession


class UserSessionManagerNode(Node):
    
    def __init__(self):
        super().__init__('user_session_manager_node')
        
        # Session storage
        self.active_sessions = {}
        
        # Services
        self.create_session_srv = self.create_service(
            CreateSession, '/session/create_voice_session',
            self.create_session_callback)
        
        self.close_session_srv = self.create_service(
            CloseSession, '/session/close_session',
            self.close_session_callback)
        
        self.get_logger().info('User Session Manager Node initialized')
    
    def create_session_callback(self, request, response):
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            'user_id': request.user_id,
            'session_type': request.session_type,
            'created_at': self.get_clock().now()
        }
        
        response.session_id = session_id
        response.qr_code_url = f'http://192.168.1.100:5000/voice/{session_id}'
        response.success = True
        
        self.get_logger().info(f'Session created: {session_id}')
        return response
    
    def close_session_callback(self, request, response):
        """Close an active user session"""
        if request.session_id in self.active_sessions:
            del self.active_sessions[request.session_id]
            response.success = True
            response.message = 'Session closed successfully'
            self.get_logger().info(f'Session closed: {request.session_id}')
        else:
            response.success = False
            response.message = 'Session not found'
        
        return response


def main(args=None):
    rclpy.init(args=args)
    node = UserSessionManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
