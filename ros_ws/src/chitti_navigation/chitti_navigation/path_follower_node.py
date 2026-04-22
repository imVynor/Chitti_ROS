"""
Direct Pure-Pursuit path follower that bypasses Nav2 entirely.

Subscribes to /global_path (from OSRM), computes steering via pure pursuit,
and publishes cmd_vel directly to the diff_drive_controller with BEST_EFFORT
QoS to match the ros2_control subscription.

This eliminates the QoS mismatch that was silently dropping all Nav2 commands.
"""

import math

import rclpy
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Path, Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import tf2_ros


class DirectPathFollower(Node):

    def __init__(self):
        super().__init__('path_follower_node')

        # ── Parameters ──────────────────────────────────────────────
        self.declare_parameter('linear_speed', 0.20)       # m/s forward
        self.declare_parameter('max_angular_speed', 1.0)   # rad/s max turn
        self.declare_parameter('lookahead_dist', 0.6)      # metres ahead
        self.declare_parameter('goal_tolerance', 0.3)       # metres to goal
        self.declare_parameter('control_rate', 10.0)        # Hz

        self.linear_speed = self.get_parameter('linear_speed').value
        self.max_angular = self.get_parameter('max_angular_speed').value
        self.lookahead = self.get_parameter('lookahead_dist').value
        self.goal_tol = self.get_parameter('goal_tolerance').value
        rate = self.get_parameter('control_rate').value

        # ── State ───────────────────────────────────────────────────
        self.path_poses = []       # list of (x, y) in odom frame
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.have_odom = False
        self.active = False        # are we currently following a path?

        # ── Publishers ──────────────────────────────────────────────
        # CRITICAL: use RELIABLE to match diff_drive_controller's expectation in Jazzy
        cmd_vel_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.cmd_pub = self.create_publisher(
            Twist, '/diff_drive_controller/cmd_vel', cmd_vel_qos
        )

        # ── Subscribers ─────────────────────────────────────────────
        self.path_sub = self.create_subscription(
            Path, '/global_path', self.path_callback, 10
        )

        # Subscribe to odometry from diff_drive_controller
        odom_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.odom_sub = self.create_subscription(
            Odometry, '/diff_drive_controller/odom', self.odom_callback, odom_qos
        )

        # Also try the EKF filtered odometry
        self.odom_sub2 = self.create_subscription(
            Odometry, '/odometry/filtered', self.odom_callback, 10
        )

        # ── Control loop timer ──────────────────────────────────────
        self.control_timer = self.create_timer(1.0 / rate, self.control_loop)

        self.get_logger().info(
            f'DirectPathFollower started: speed={self.linear_speed} m/s, '
            f'lookahead={self.lookahead} m, publishing cmd_vel with BEST_EFFORT QoS'
        )

    # ─────────────────────────────────────────────────────────────────
    #  Callbacks
    # ─────────────────────────────────────────────────────────────────

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        # Extract yaw from quaternion
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)
        self.have_odom = True

    def path_callback(self, msg: Path):
        if len(msg.poses) < 2:
            self.get_logger().warn('Received path with < 2 poses, ignoring.')
            return

        self.path_poses = [
            (p.pose.position.x, p.pose.position.y) for p in msg.poses
        ]
        self.active = True
        self.get_logger().info(
            f'New path received with {len(self.path_poses)} waypoints. '
            f'Following directly (bypassing Nav2).'
        )

    # ─────────────────────────────────────────────────────────────────
    #  Pure pursuit control loop
    # ─────────────────────────────────────────────────────────────────

    def control_loop(self):
        if not self.active or not self.path_poses:
            return

        if not self.have_odom:
            # No odometry yet — send zero and wait
            self.get_logger().info(
                'Waiting for odometry on /diff_drive_controller/odom or '
                '/odometry/filtered ...', throttle_duration_sec=5.0
            )
            return

        # Check if we reached the final goal
        gx, gy = self.path_poses[-1]
        dist_to_goal = math.hypot(gx - self.robot_x, gy - self.robot_y)
        if dist_to_goal < self.goal_tol:
            self.get_logger().info('Reached goal! Stopping.')
            self.active = False
            self.path_poses = []
            self._publish_stop()
            return

        # Find the lookahead point on the path
        lookahead_pt = self._find_lookahead_point()
        if lookahead_pt is None:
            self.get_logger().warn('No lookahead point found, stopping.')
            self._publish_stop()
            return

        # Compute steering angle via pure pursuit
        lx, ly = lookahead_pt
        dx = lx - self.robot_x
        dy = ly - self.robot_y
        target_angle = math.atan2(dy, dx)
        angle_error = self._normalize_angle(target_angle - self.robot_yaw)

        # If we need to turn a lot, rotate in place first
        cmd = Twist()
        if abs(angle_error) > 0.8:  # ~45 degrees
            cmd.linear.x = 0.0
            cmd.angular.z = max(-self.max_angular,
                                min(self.max_angular, angle_error * 2.0))
        else:
            cmd.linear.x = self.linear_speed
            # Pure pursuit curvature: angular = 2 * sin(alpha) / L
            L = math.hypot(dx, dy)
            if L > 0.01:
                curvature = 2.0 * math.sin(angle_error) / L
                cmd.angular.z = max(-self.max_angular,
                                    min(self.max_angular,
                                        self.linear_speed * curvature))

        self.cmd_pub.publish(cmd)

    def _find_lookahead_point(self):
        """Find the point on the path that is ~lookahead_dist ahead."""
        best_idx = 0
        best_dist = float('inf')

        # Find closest point on path to robot
        for i, (px, py) in enumerate(self.path_poses):
            d = math.hypot(px - self.robot_x, py - self.robot_y)
            if d < best_dist:
                best_dist = d
                best_idx = i

        # Walk forward along the path until we reach lookahead distance
        for i in range(best_idx, len(self.path_poses)):
            px, py = self.path_poses[i]
            d = math.hypot(px - self.robot_x, py - self.robot_y)
            if d >= self.lookahead:
                return (px, py)

        # If we can't find a point far enough ahead, use the last point
        if self.path_poses:
            return self.path_poses[-1]
        return None

    def _publish_stop(self):
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_pub.publish(cmd)

    @staticmethod
    def _normalize_angle(angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle


def main(args=None):
    rclpy.init(args=args)
    node = DirectPathFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
