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
            'library':        {'name': 'Central Library', 'lat': 23.213556, 'lon': 72.686485},
            'jibaben':        {'name': 'Jibaben',         'lat': 23.214793, 'lon': 72.685498},
            'jasubhai':       {'name': 'Jasubhai',         'lat': 23.214685, 'lon': 72.685762},
            'duven':          {'name': 'Duven Hostel',     'lat': 23.210695, 'lon': 72.685313},
            'sports_complex': {'name': 'Sports Complex',   'lat': 23.211714, 'lon': 72.687882},
            'guest_house':    {'name': 'Guest House',      'lat': 23.211416, 'lon': 72.689919},
            'jaiswal_mess':   {'name': 'Jaiswal Mess',     'lat': 23.210932, 'lon': 72.683778},
            'new_pc':         {'name': 'New PC',            'lat': 23.209977, 'lon': 72.684410},
            'rangmanch':      {'name': 'Rangmanch',         'lat': 23.216262, 'lon': 72.687482},
            'gate_1':         {'name': 'Gate 1',            'lat': 23.215753, 'lon': 72.693079},
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
