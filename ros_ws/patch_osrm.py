import re

with open('/home/anubhav-gupta/Chitti/ros_ws/src/chitti_navigation/chitti_navigation/osrm_path_node.py', 'r') as f:
    content = f.read()

# Add imports
if 'from visualization_msgs.msg import Marker' not in content:
    content = content.replace('from nav_msgs.msg import Odometry, Path',
                              'from nav_msgs.msg import Odometry, Path\nfrom visualization_msgs.msg import Marker\nfrom geometry_msgs.msg import Point\nfrom rclpy.qos import QoSProfile, QoSDurabilityPolicy')

# Add publisher
init_addition = """
        qos_profile = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.map_pub = self.create_publisher(Marker, '/campus_map_marker', qos_profile)
"""
if 'self.map_pub = self.create_publisher' not in content:
    content = content.replace('self.path_pub = self.create_publisher(Path, \'/global_path\', 10)',
                              'self.path_pub = self.create_publisher(Path, \'/global_path\', 10)\n' + init_addition)


# Call publish_map_marker at the end of load_campus_map
if 'self.publish_map_marker()' not in content:
    content = content.replace("f'Campus map loaded: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges'\n            )",
                              "f'Campus map loaded: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges'\n            )\n            self.publish_map_marker()")


# Add publish_map_marker method
method_addition = """
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
"""
if 'def publish_map_marker' not in content:
    content += method_addition

with open('/home/anubhav-gupta/Chitti/ros_ws/src/chitti_navigation/chitti_navigation/osrm_path_node.py', 'w') as f:
    f.write(content)

