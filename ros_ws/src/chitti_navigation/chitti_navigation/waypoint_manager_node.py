# Waypoint Manager Node
import rclpy
from rclpy.node import Node
from chitti_msgs.msg import TourStatus


class WaypointManagerNode(Node):
    
    def __init__(self):
        super().__init__('waypoint_manager_node')
        
        # Tour routes
        self.tour_routes = {
            'academic_tour': ['academic_block', 'library', 'admin'],
            'campus_highlights': ['academic_block', 'library', 'cafeteria', 'auditorium'],
            'full_campus': ['academic_block', 'library', 'cafeteria', 'hostels', 'admin', 'auditorium'],
        }
        
        # Publishers
        self.tour_status_pub = self.create_publisher(TourStatus, '/tour/status', 10)
        
        self.get_logger().info('Waypoint Manager Node initialized')
    
    def get_tour_waypoints(self, tour_id: str):
        """Get waypoints for a specific tour"""
        return self.tour_routes.get(tour_id, [])


def main(args=None):
    rclpy.init(args=args)
    node = WaypointManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
