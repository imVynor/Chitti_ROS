import math
import os
import argparse
import threading
import time

from flask import Flask, jsonify, render_template, request
try:
    from flask_cors import CORS
except ImportError:
    def CORS(_app):
        return _app

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Path
from geometry_msgs.msg import TwistStamped

from chitti_msgs.msg import LocationRequest

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
)
CORS(app)


DESTINATION_OPTIONS = {
    'academic_block_7': {'name': 'Academic Block 7', 'lat': 23.213911122480645, 'lon': 72.68500570339303},
    'library': {'name': 'Central Library', 'lat': 23.214198501380685, 'lon': 72.68666461800079},
    'cafeteria': {'name': '2 Degree Cafeteria', 'lat': 23.2157075206042, 'lon': 72.68489108176994},
    'duven': {'name': 'Duven Hostel', 'lat': 23.211117893794628, 'lon': 72.68532067680564},
    'jasubhai': {'name': 'Main Auditorium (Jasubhai)', 'lat': 23.214768335496007, 'lon': 72.68584071838407},
}

MAP_BOUNDS = {
    'lat_min': 23.210441193660797,
    'lat_max': 23.216741193660797,
    'lon_min': 72.68376270371092,
    'lon_max': 72.68726270371092,
}

MAP_CONFIG = {
    'center_lat': 23.213911122480645,
    'center_lon': 72.68500570339303,
    'min_zoom': 15,
    'max_zoom': 19,
}


def haversine_meters(lat1, lon1, lat2, lon2):
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius * c


class HMIRosBridge(Node):
    def __init__(self):
        super().__init__('hmi_web_bridge')

        vel_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.destination_pub = self.create_publisher(LocationRequest, '/ui/destination_selected', 10)
        self.goal_pub = self.create_publisher(NavSatFix, '/goal_gps', 10)
        self.motor_cmd_pub = self.create_publisher(TwistStamped, '/diff_drive_controller/cmd_vel', vel_qos)
        self.nav_cmd_sub = self.create_subscription(TwistStamped, '/nav2_cmd_vel', self.nav_cmd_callback, vel_qos)
        self.fix_sub = self.create_subscription(NavSatFix, '/fix', self.fix_callback, 10)
        self.path_sub = self.create_subscription(Path, '/global_path', self.path_callback, 10)

        self.current_position = None
        self.active_goal = None
        self.selected_destination = None
        self.initial_distance_m = 0.0
        self.navigation_active = False
        self.goal_set_time = None
        self.latest_path_distance_m = None
        self.latest_path_pose_count = 0
        self.latest_path_latlon = []
        self.robot_history = []

        # Keep datum aligned with navigation nodes that publish /global_path in map frame.
        self.datum_lat = 23.2139111
        self.datum_lon = 72.6850057
        self.max_linear_speed = 0.45
        self.max_angular_speed = 1.8
        self.manual_override_until = 0.0

    def nav_cmd_callback(self, msg):
        # Manual UI commands temporarily override Nav2 output to avoid command fights.
        if time.monotonic() < self.manual_override_until:
            return
        self.motor_cmd_pub.publish(msg)

    def path_callback(self, msg):
        if not msg.poses:
            self.latest_path_distance_m = None
            self.latest_path_pose_count = 0
            self.latest_path_latlon = []
            return

        total = 0.0
        latlon_points = []
        cos_lat = math.cos(math.radians(self.datum_lat))

        for pose in msg.poses:
            x = float(pose.pose.position.x)
            y = float(pose.pose.position.y)
            lat = self.datum_lat + (y / 111320.0)
            lon = self.datum_lon + (x / (111320.0 * cos_lat))
            latlon_points.append((round(lat, 6), round(lon, 6)))

        for i in range(1, len(msg.poses)):
            p_prev = msg.poses[i - 1].pose.position
            p_cur = msg.poses[i].pose.position
            total += math.hypot(p_cur.x - p_prev.x, p_cur.y - p_prev.y)

        self.latest_path_distance_m = total
        self.latest_path_pose_count = len(msg.poses)
        self.latest_path_latlon = latlon_points

    def fix_callback(self, msg):
        self.current_position = {'lat': float(msg.latitude), 'lon': float(msg.longitude)}
        self.robot_history.append((self.current_position['lat'], self.current_position['lon']))
        if len(self.robot_history) > 300:
            self.robot_history = self.robot_history[-300:]

    def _publish_destination(self, location_id, location_name, lat, lon):
        location_msg = LocationRequest()
        location_msg.location_id = location_id
        location_msg.location_name = location_name
        location_msg.coordinates.x = float(lat)
        location_msg.coordinates.y = float(lon)
        location_msg.coordinates.z = 0.0
        location_msg.urgent = False
        location_msg.accessibility_requirements = ''
        self.destination_pub.publish(location_msg)

        goal_msg = NavSatFix()
        goal_msg.header.stamp = self.get_clock().now().to_msg()
        goal_msg.header.frame_id = 'map'
        goal_msg.latitude = float(lat)
        goal_msg.longitude = float(lon)
        goal_msg.altitude = 0.0
        self.goal_pub.publish(goal_msg)

        self.active_goal = {'lat': float(lat), 'lon': float(lon), 'name': location_name}
        self.selected_destination = location_id
        self.navigation_active = True
        self.goal_set_time = time.monotonic()
        self.latest_path_distance_m = None
        self.latest_path_pose_count = 0
        self.latest_path_latlon = []
        self.robot_history = []

        if self.current_position is not None:
            self.initial_distance_m = haversine_meters(
                self.current_position['lat'],
                self.current_position['lon'],
                self.active_goal['lat'],
                self.active_goal['lon'],
            )
        else:
            # Use campus center as simulated robot start when no live fix exists.
            self.initial_distance_m = haversine_meters(
                23.213911122480645,
                72.68500570339303,
                self.active_goal['lat'],
                self.active_goal['lon'],
            )

    def select_predefined(self, location_id):
        option = DESTINATION_OPTIONS.get(location_id)
        if option is None:
            return False, 'Unknown destination option'

        self._publish_destination(location_id, option['name'], option['lat'], option['lon'])
        return True, f"Navigation started to {option['name']}"

    def select_from_screen(self, x_ratio, y_ratio):
        x_ratio = min(max(float(x_ratio), 0.0), 1.0)
        y_ratio = min(max(float(y_ratio), 0.0), 1.0)

        lon = MAP_BOUNDS['lon_min'] + (x_ratio * (MAP_BOUNDS['lon_max'] - MAP_BOUNDS['lon_min']))
        lat = MAP_BOUNDS['lat_max'] - (y_ratio * (MAP_BOUNDS['lat_max'] - MAP_BOUNDS['lat_min']))

        label = f'Custom Point ({lat:.6f}, {lon:.6f})'
        self._publish_destination('custom_point', label, lat, lon)
        return True, 'Custom destination selected from map'

    def select_latlon(self, lat, lon):
        label = f'Custom Point ({lat:.6f}, {lon:.6f})'
        self._publish_destination('custom_point', label, lat, lon)
        return True, 'Navigation started to selected IITGN map point'

    def publish_motion_command(self, linear_x, angular_z):
        linear_x = max(-self.max_linear_speed, min(self.max_linear_speed, float(linear_x)))
        angular_z = max(-self.max_angular_speed, min(self.max_angular_speed, float(angular_z)))

        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_footprint'
        cmd.twist.linear.x = linear_x
        cmd.twist.angular.z = angular_z
        self.manual_override_until = time.monotonic() + 0.8
        self.motor_cmd_pub.publish(cmd)

        return {
            'linear_x': round(linear_x, 3),
            'angular_z': round(angular_z, 3),
        }

    def get_navigation_status(self):
        remaining_distance = None
        simulated_remaining = None
        if self.navigation_active and self.active_goal is not None:
            if self.initial_distance_m > 0.0 and self.goal_set_time is not None:
                elapsed = max(0.0, time.monotonic() - self.goal_set_time)
                simulated_speed_mps = 0.9
                simulated_remaining = max(0.0, self.initial_distance_m - (elapsed * simulated_speed_mps))

            if self.current_position is not None:
                live_remaining = haversine_meters(
                    self.current_position['lat'],
                    self.current_position['lon'],
                    self.active_goal['lat'],
                    self.active_goal['lon'],
                )
                if simulated_remaining is None:
                    remaining_distance = live_remaining
                else:
                    # In simulation, allow progress even when fake GPS is static.
                    remaining_distance = min(live_remaining, simulated_remaining)
            else:
                remaining_distance = simulated_remaining

        eta_seconds = None
        if remaining_distance is not None:
            simulated_speed_mps = 0.9
            eta_seconds = remaining_distance / simulated_speed_mps

            if remaining_distance < 2.0:
                self.navigation_active = False

        planned_distance = self.latest_path_distance_m
        if planned_distance is None:
            planned_distance = self.initial_distance_m

        return {
            'navigation_active': self.navigation_active,
            'selected_destination': self.selected_destination,
            'goal': self.active_goal,
            'robot_position': self.current_position,
            'robot_history': [{'lat': lat, 'lon': lon} for lat, lon in self.robot_history],
            'path_available': self.latest_path_distance_m is not None,
            'path_pose_count': self.latest_path_pose_count,
            'path_points': [{'lat': lat, 'lon': lon} for lat, lon in self.latest_path_latlon],
            'planned_distance_m': round(planned_distance, 2),
            'remaining_distance_m': round(remaining_distance, 2) if remaining_distance is not None else None,
            'eta_seconds': round(eta_seconds, 1) if eta_seconds is not None else None,
        }


ros_bridge = None


def start_ros_bridge():
    global ros_bridge
    try:
        rclpy.init(args=None)
        ros_bridge = HMIRosBridge()
        executor = MultiThreadedExecutor()
        executor.add_node(ros_bridge)

        thread = threading.Thread(target=executor.spin, daemon=True)
        thread.start()
    except Exception as exc:
        print(f'ROS bridge startup failed: {exc}')
        ros_bridge = None


@app.route('/')
def index():
    return render_template('voice_input.html')


@app.route('/voice/<session_id>')
def voice_interface(session_id):
    """Voice input interface for specific session"""
    return render_template('voice_input.html')


@app.route('/api/options', methods=['GET'])
def get_options():
    return jsonify({
        'map': {
            **MAP_CONFIG,
            **MAP_BOUNDS,
        },
        'options': [
            {'id': key, 'name': value['name'], 'lat': value['lat'], 'lon': value['lon']}
            for key, value in DESTINATION_OPTIONS.items()
        ]
    })


@app.route('/api/navigation/select-option', methods=['POST'])
def select_option():
    if ros_bridge is None:
        return jsonify({'status': 'error', 'message': 'ROS bridge unavailable'}), 503

    payload = request.get_json(silent=True) or {}
    location_id = payload.get('location_id', '')
    success, message = ros_bridge.select_predefined(location_id)
    status_code = 200 if success else 400
    return jsonify({'status': 'success' if success else 'error', 'message': message}), status_code


@app.route('/api/navigation/select-point', methods=['POST'])
def select_point():
    if ros_bridge is None:
        return jsonify({'status': 'error', 'message': 'ROS bridge unavailable'}), 503

    payload = request.get_json(silent=True) or {}
    x_ratio = payload.get('x')
    y_ratio = payload.get('y')
    if x_ratio is None or y_ratio is None:
        return jsonify({'status': 'error', 'message': 'x and y are required'}), 400

    success, message = ros_bridge.select_from_screen(x_ratio, y_ratio)
    status_code = 200 if success else 400
    return jsonify({'status': 'success' if success else 'error', 'message': message}), status_code


@app.route('/api/navigation/select-latlon', methods=['POST'])
def select_latlon():
    if ros_bridge is None:
        return jsonify({'status': 'error', 'message': 'ROS bridge unavailable'}), 503

    payload = request.get_json(silent=True) or {}
    lat = payload.get('lat')
    lon = payload.get('lon')
    if lat is None or lon is None:
        return jsonify({'status': 'error', 'message': 'lat and lon are required'}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'lat/lon must be numeric'}), 400

    if not (MAP_BOUNDS['lat_min'] <= lat <= MAP_BOUNDS['lat_max'] and MAP_BOUNDS['lon_min'] <= lon <= MAP_BOUNDS['lon_max']):
        return jsonify({'status': 'error', 'message': 'Selected point is outside IITGN campus bounds'}), 400

    success, message = ros_bridge.select_latlon(lat, lon)
    status_code = 200 if success else 400
    return jsonify({'status': 'success' if success else 'error', 'message': message}), status_code


@app.route('/api/navigation/status', methods=['GET'])
def navigation_status():
    if ros_bridge is None:
        return jsonify({'status': 'error', 'message': 'ROS bridge unavailable'}), 503

    return jsonify({'status': 'success', 'navigation': ros_bridge.get_navigation_status()})


@app.route('/api/motion/command', methods=['POST'])
def motion_command():
    if ros_bridge is None:
        return jsonify({'status': 'error', 'message': 'ROS bridge unavailable'}), 503

    payload = request.get_json(silent=True) or {}
    linear = payload.get('linear', 0.0)
    angular = payload.get('angular', 0.0)

    try:
        command = ros_bridge.publish_motion_command(linear, angular)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'linear/angular must be numeric'}), 400
    except Exception as exc:
        app.logger.exception('Failed to publish motion command')
        return jsonify({'status': 'error', 'message': f'motion publish failed: {exc}'}), 500

    return jsonify({'status': 'success', 'command': command})


@app.route('/api/motion/stop', methods=['POST'])
def motion_stop():
    if ros_bridge is None:
        return jsonify({'status': 'error', 'message': 'ROS bridge unavailable'}), 503

    try:
        command = ros_bridge.publish_motion_command(0.0, 0.0)
    except Exception as exc:
        app.logger.exception('Failed to publish stop command')
        return jsonify({'status': 'error', 'message': f'stop publish failed: {exc}'}), 500

    return jsonify({'status': 'success', 'command': command, 'message': 'Stop command sent'})


@app.route('/api/voice', methods=['POST'])
def process_voice():
    """Handle voice input"""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'message': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'unknown')
        
        # Here audio would be processed by external service
        # For now, just acknowledge receipt
        return jsonify({
            'status': 'success',
            'message': 'Audio received',
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'ros_bridge': ros_bridge is not None})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chitti HMI web interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind web interface')
    parser.add_argument('--port', default=5000, type=int, help='Port to bind web interface')
    args = parser.parse_args()

    start_ros_bridge()
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
