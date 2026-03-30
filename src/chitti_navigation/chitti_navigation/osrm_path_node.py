import math

import networkx as nx
import osmnx as ox
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix


class OSRMPathNode(Node):

    def __init__(self):
        super().__init__('osrm_path_node')

        self.current_lat = None
        self.current_lon = None
        self.graph = None

        self.path_pub = self.create_publisher(Path, '/global_path', 10)
        self.goal_sub = self.create_subscription(NavSatFix, '/goal_gps', self.goal_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        self.fix_sub = self.create_subscription(NavSatFix, '/fix', self.fix_callback, 10)

        self.get_logger().info('Loading IIT Gandhinagar campus map...')
        self.load_campus_map()
        self.get_logger().info('Map loaded. Send /goal_gps to plan routes.')

    def load_campus_map(self):
        try:
            ox.settings.max_query_area_size = 50_000_000
            self.graph = ox.graph_from_point(
                center_point=(23.2114, 72.6842),
                dist=800,
                network_type='all',
                retain_all=False,
                simplify=True,
            )
            self.get_logger().info(
                f'Campus map loaded: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges'
            )
        except Exception as exc:
            self.get_logger().error(f'Failed to load campus map: {exc}')

    def fix_callback(self, msg):
        # Fallback current position when odometry/localization is unavailable.
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    def odom_callback(self, msg):
        datum_lat = 23.2164
        datum_lon = 72.6836
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        self.current_lat = datum_lat + (y / 111320.0)
        self.current_lon = datum_lon + (
            x / (111320.0 * math.cos(math.radians(datum_lat)))
        )

    def goal_callback(self, msg):
        if self.graph is None:
            self.get_logger().error('Map not loaded yet')
            return

        if self.current_lat is None or self.current_lon is None:
            self.get_logger().error('Current robot position unknown (/odometry/filtered or /fix needed)')
            return

        self.plan_and_publish(
            self.current_lat,
            self.current_lon,
            msg.latitude,
            msg.longitude,
        )

    def plan_and_publish(self, start_lat, start_lon, end_lat, end_lon):
        try:
            start_node = ox.distance.nearest_nodes(self.graph, start_lon, start_lat)
            end_node = ox.distance.nearest_nodes(self.graph, end_lon, end_lat)

            if start_node == end_node:
                self.get_logger().warn('Start and end snapped to same graph node')
                return

            route = nx.shortest_path(self.graph, start_node, end_node, weight='length')
            path_msg = self.route_to_path_msg(route)
            self.path_pub.publish(path_msg)
            self.get_logger().info(
                f'Published /global_path with {len(path_msg.poses)} poses'
            )
        except nx.NetworkXNoPath:
            self.get_logger().error('No graph path found between start and goal')
        except Exception as exc:
            self.get_logger().error(f'Path planning failed: {exc}')

    def route_to_path_msg(self, route):
        datum_lat = 23.2164
        datum_lon = 72.6836

        path_msg = Path()
        path_msg.header.frame_id = 'map'
        path_msg.header.stamp = self.get_clock().now().to_msg()

        for node_id in route:
            node_data = self.graph.nodes[node_id]
            node_lat = node_data['y']
            node_lon = node_data['x']

            x = (node_lon - datum_lon) * 111320.0 * math.cos(math.radians(datum_lat))
            y = (node_lat - datum_lat) * 111320.0

            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0
            path_msg.poses.append(pose)

        return path_msg


def main(args=None):
    rclpy.init(args=args)
    node = OSRMPathNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
