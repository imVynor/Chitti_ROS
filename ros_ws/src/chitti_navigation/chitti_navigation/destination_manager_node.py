import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from chitti_msgs.msg import LocationRequest, RobotLocation
from chitti_msgs.srv import StartNavigation


class DestinationManagerNode(Node):

    def __init__(self):
        super().__init__('destination_manager_node')

        # Chitti location IDs mapped to GPS coordinates used by the friend planner.
        self.locations = {
            'academic_block': {'name': 'Academic Block', 'lat': 23.212041193660797, 'lon': 72.68396270371093},
            'academic_block_7': {'name': 'Academic Block 7', 'lat': 23.213911122480645, 'lon': 72.68500570339303},
            'library': {'name': 'Central Library', 'lat': 23.214198501380685, 'lon': 72.68666461800079},
            'cafeteria': {'name': 'Cafeteria', 'lat': 23.2113411936608, 'lon': 72.68486270371091},
            'hostels': {'name': 'Student Hostels', 'lat': 23.212341193660798, 'lon': 72.68446270371092},
            'duven': {'name': 'Duven Hostel', 'lat': 23.211117893794628, 'lon': 72.68532067680564},
            'admin': {'name': 'Administration Block', 'lat': 23.213041193660797, 'lon': 72.68436270371092},
            'auditorium': {'name': 'Main Auditorium', 'lat': 23.214802193660797, 'lon': 72.68584270371092},
            'jasubhai': {'name': 'Main Auditorium (Jasubhai)', 'lat': 23.214768335496007, 'lon': 72.68584071838407},
        }

        self.location_pub = self.create_publisher(RobotLocation, '/robot/current_location', 10)
        self.goal_pub = self.create_publisher(NavSatFix, '/goal_gps', 10)

        self.destination_sub = self.create_subscription(
            LocationRequest, '/ui/destination_selected',
            self.destination_callback, 10)

        self.navigate_service = self.create_service(
            StartNavigation, '/navigation/start_to_location',
            self.start_navigation_callback)

        self.get_logger().info('Destination Manager adapter initialized')

    def _publish_goal(self, location_id: str) -> bool:
        location = self.locations.get(location_id)
        if location is None:
            return False

        goal = NavSatFix()
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.header.frame_id = 'map'
        goal.latitude = float(location['lat'])
        goal.longitude = float(location['lon'])
        goal.altitude = 0.0
        self.goal_pub.publish(goal)

        status = RobotLocation()
        status.current_zone = location_id
        status.nearest_landmark = location['name']
        status.battery_percentage = 100.0
        status.navigation_active = True
        self.location_pub.publish(status)
        return True

    def destination_callback(self, msg):
        self.get_logger().info(f'Destination selected: {msg.location_id}')
        if not self._publish_goal(msg.location_id):
            self.get_logger().warn(f'Unknown destination id: {msg.location_id}')

    def start_navigation_callback(self, request, response):
        if self._publish_goal(request.destination_id):
            destination = self.locations[request.destination_id]['name']
            response.success = True
            response.message = f'Starting navigation to {destination}'
            response.estimated_duration = 5.0
        else:
            response.success = False
            response.message = 'Destination not found'
            response.estimated_duration = 0.0

        return response


def main(args=None):
    rclpy.init(args=args)
    node = DestinationManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
