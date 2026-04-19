# Tour Manager Node
import rclpy
from rclpy.node import Node
from chitti_msgs.msg import TourStatus


class TourManagerNode(Node):
    
    def __init__(self):
        super().__init__('tour_manager_node')
        
        # Tour routes
        self.tour_routes = {
            'campus_highlights': {
                'name': 'Campus Highlights',
                'locations': ['library', 'jasubhai', 'sports_complex', 'rangmanch'],
                'duration': 45
            },
            'full_campus': {
                'name': 'Complete Campus Tour',
                'locations': ['library', 'jibaben', 'jasubhai', 'duven', 'sports_complex', 'guest_house', 'rangmanch', 'gate_1'],
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
