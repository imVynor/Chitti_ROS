import math

import networkx as nx
import osmnx as ox
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from rclpy.qos import QoSProfile, QoSDurabilityPolicy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix


class OSRMPathNode(Node):

    def __init__(self):
        super().__init__('osrm_path_node')

        self.default_lat = 23.213911122480645
        self.default_lon = 72.68500570339303
        self.current_lat = self.default_lat
        self.current_lon = self.default_lon
        self.graph = None
        self.routing_graph = None

        self.path_pub = self.create_publisher(Path, '/global_path', 10)

        qos_profile = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.map_pub = self.create_publisher(Marker, '/campus_map_marker', qos_profile)

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
                dist=2000,
                network_type='all',
                retain_all=False,
                simplify=True,
            )
            # Use an undirected view for shortest-path routing so one-way tagging
            # does not block valid campus traversal in this local planner.
            self.routing_graph = self.graph.to_undirected(as_view=False)
            self.get_logger().info(
                f'Campus map loaded: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges'
            )
            self.publish_map_marker()
        except Exception as exc:
            self.get_logger().error(f'Failed to load campus map: {exc}')

    def fix_callback(self, msg):
        # Fallback current position when odometry/localization is unavailable.
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    def odom_callback(self, msg):
        if msg.header.frame_id != 'map':
            # Ignore odometry if it is not in the map frame (e.g., odom frame)
            # We will rely on /fix instead for global position.
            return

        datum_lat = 23.2164
        datum_lon = 72.6836
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        self.current_lat = datum_lat + (y / 111320.0)
        self.current_lon = datum_lon + (
            x / (111320.0 * math.cos(math.radians(datum_lat)))
        )

    def goal_callback(self, msg):
        if self.graph is None or self.routing_graph is None:
            self.get_logger().error('Map not loaded yet')
            return

        if self.current_lat is None or self.current_lon is None:
            self.get_logger().warn('Current position unavailable. Using default campus start position.')
            self.current_lat = self.default_lat
            self.current_lon = self.default_lon

        self.plan_and_publish(
            self.current_lat,
            self.current_lon,
            msg.latitude,
            msg.longitude,
        )

    def plan_and_publish(self, start_lat, start_lon, end_lat, end_lon):
        try:
            start_node = ox.distance.nearest_nodes(self.routing_graph, start_lon, start_lat)
            end_node = ox.distance.nearest_nodes(self.routing_graph, end_lon, end_lat)

            self.get_logger().info(
                f'Planning route start=({start_lat:.6f},{start_lon:.6f}) '
                f'goal=({end_lat:.6f},{end_lon:.6f}) start_node={start_node} end_node={end_node}'
            )

            if start_node == end_node:
                self.get_logger().warn('Start and end snapped to same graph node, publishing direct 2-point path')
                path_msg = self.route_to_path_msg([], start_lat, start_lon, end_lat, end_lon)
                self.path_pub.publish(path_msg)
                return

            route = nx.shortest_path(self.routing_graph, start_node, end_node, weight='length')
            path_msg = self.route_to_path_msg(route, start_lat, start_lon, end_lat, end_lon)
            self.path_pub.publish(path_msg)
            
            # Publish visual markers for START and GOAL to debug RViz perception
            from visualization_msgs.msg import MarkerArray
            if not hasattr(self, 'label_pub'):
                self.label_pub = self.create_publisher(MarkerArray, '/path_labels', 10)
                
            arr = MarkerArray()
            
            # Start Marker
            m_start = Marker()
            m_start.header.frame_id = 'map'
            m_start.header.stamp = self.get_clock().now().to_msg()
            m_start.ns = 'labels'
            m_start.id = 1
            m_start.type = Marker.TEXT_VIEW_FACING
            m_start.action = Marker.ADD
            m_start.pose.position = path_msg.poses[0].pose.position
            m_start.pose.position.z = 2.0
            m_start.scale.z = 10.0
            m_start.color.a = 1.0
            m_start.color.r, m_start.color.g, m_start.color.b = 0.0, 1.0, 0.0
            m_start.text = "ROBOT (START)"
            
            # End Marker
            m_end = Marker()
            m_end.header.frame_id = 'map'
            m_end.header.stamp = self.get_clock().now().to_msg()
            m_end.ns = 'labels'
            m_end.id = 2
            m_end.type = Marker.TEXT_VIEW_FACING
            m_end.action = Marker.ADD
            m_end.pose.position = path_msg.poses[-1].pose.position
            m_end.pose.position.z = 2.0
            m_end.scale.z = 10.0
            m_end.color.a = 1.0
            m_end.color.r, m_end.color.g, m_end.color.b = 1.0, 0.0, 0.0
            m_end.text = "DESTINATION (END)"
            
            arr.markers = [m_start, m_end]
            self.label_pub.publish(arr)

            self.get_logger().info(
                f'Published /global_path with {len(path_msg.poses)} poses'
            )
        except nx.NetworkXNoPath:
            self.get_logger().error('No graph path found between start and goal')
        except Exception as exc:
            self.get_logger().error(f'Path planning failed: {exc}')

    def route_to_path_msg(self, route, start_lat, start_lon, end_lat, end_lon):
        datum_lat = 23.2164
        datum_lon = 72.6836

        path_msg = Path()
        path_msg.header.frame_id = 'map'
        path_msg.header.stamp = self.get_clock().now().to_msg()
        
        def create_pose(node_lat, node_lon):
            x = (node_lon - datum_lon) * 111320.0 * math.cos(math.radians(datum_lat))
            y = (node_lat - datum_lat) * 111320.0
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0
            return pose

        # Add the exact start position
        path_msg.poses.append(create_pose(start_lat, start_lon))

        for i in range(len(route) - 1):
            u = route[i]
            v = route[i+1]
            node_u = self.graph.nodes[u]
            path_msg.poses.append(create_pose(node_u['y'], node_u['x']))
            
            # Follow edge geometry precisely to avoid cutting through buildings/grass
            edge_data = self.graph.get_edge_data(u, v, 0)
            if edge_data and 'geometry' in edge_data:
                coords = list(edge_data['geometry'].coords)
                # Skip first and last as they are the node centres
                for lon, lat in coords[1:-1]:
                    path_msg.poses.append(create_pose(lat, lon))
        
        # Add the final road node
        if route:
            end_node = self.graph.nodes[route[-1]]
            path_msg.poses.append(create_pose(end_node['y'], end_node['x']))

        # Add the exact end position
        path_msg.poses.append(create_pose(end_lat, end_lon))

        # Calculate yaw and orientation for each pose to make RViz arrows point correctly
        for i in range(len(path_msg.poses) - 1):
            dx = path_msg.poses[i+1].pose.position.x - path_msg.poses[i].pose.position.x
            dy = path_msg.poses[i+1].pose.position.y - path_msg.poses[i].pose.position.y
            yaw = math.atan2(dy, dx)
            
            # Convert yaw to quaternion (roll=0, pitch=0)
            path_msg.poses[i].pose.orientation.x = 0.0
            path_msg.poses[i].pose.orientation.y = 0.0
            path_msg.poses[i].pose.orientation.z = math.sin(yaw / 2.0)
            path_msg.poses[i].pose.orientation.w = math.cos(yaw / 2.0)

        # Ensure the final pose has the same orientation as the second to last
        if len(path_msg.poses) > 1:
            path_msg.poses[-1].pose.orientation = path_msg.poses[-2].pose.orientation

        return path_msg

    def publish_map_marker(self):
        if self.graph is None: return
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'osmnx_map'
        marker.id = 0
        marker.type = Marker.LINE_LIST
        marker.action = Marker.ADD
        marker.scale.x = 1.0  # Line width
        marker.color.a = 0.3  # Translucent
        marker.color.r, marker.color.g, marker.color.b = 1.0, 1.0, 1.0 # White

        datum_lat, datum_lon = 23.2164, 72.6836

        def get_point(n_lat, n_lon):
            x = (n_lon - datum_lon) * 111320.0 * math.cos(math.radians(datum_lat))
            y = (n_lat - datum_lat) * 111320.0
            p = Point()
            p.x, p.y, p.z = float(x), float(y), 0.0
            return p

        for u, v, data in self.graph.edges(data=True):
            node_u = self.graph.nodes[u]
            node_v = self.graph.nodes[v]
            if 'geometry' in data:
                coords = list(data['geometry'].coords)
                for i in range(len(coords)-1):
                    lon1, lat1 = coords[i]
                    lon2, lat2 = coords[i+1]
                    marker.points.append(get_point(lat1, lon1))
                    marker.points.append(get_point(lat2, lon2))
            else:
                marker.points.append(get_point(node_u['y'], node_u['x']))
                marker.points.append(get_point(node_v['y'], node_v['x']))
                
        self.map_pub.publish(marker)
        self.get_logger().info('Published street map marker to /campus_map_marker')


def main(args=None):
    rclpy.init(args=args)
    node = OSRMPathNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

