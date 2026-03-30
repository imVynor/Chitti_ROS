# Tour Manager Node
import rclpy
from rclpy.node import Node
from chitti_msgs.msg import TourStatus


class TourManagerNode(Node):
    
    def __init__(self):
        super().__init__('tour_manager_node')
        
        # Tour routes
        self.tour_routes = {
            'academic_tour': {
                'name': 'Academic Tour',
                'locations': ['academic_block', 'library', 'admin'],
                'duration': 30
            },
            'campus_highlights': {
                'name': 'Campus Highlights',
                'locations': ['academic_block', 'library', 'cafeteria', 'auditorium'],
                'duration': 45
            },
            'full_campus': {
                'name': 'Complete Campus Tour',
                'locations': ['academic_block', 'library', 'cafeteria', 'hostels', 'admin', 'auditorium'],
                'duration': 60
            }
        }
        
        # Publishers
        self.tour_status_pub = self.create_publisher(TourStatus, '/tour/status', 10)
        
        self.get_logger().info('Tour Manager Node initialized')
    
    def get_tour_info(self, tour_id: str):
        """Get tour information"""
        return self.tour_routes.get(tour_id, None)


def main(args=None):
    rclpy.init(args=args)
    node = TourManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
