import math

import rclpy
from nav2_msgs.action import FollowPath
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped, Quaternion
from rclpy.action import ActionClient
from rclpy.node import Node


class PathFollowerNode(Node):

    def __init__(self):
        super().__init__('path_follower_node')
        self._action_client = ActionClient(self, FollowPath, 'follow_path')
        self.path_sub = self.create_subscription(Path, '/global_path', self.path_callback, 10)
        self.get_logger().info('PathFollowerNode started and waiting for /global_path')

    def get_quaternion_from_yaw(self, yaw):
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q

    def interpolate_path(self, sparse_path, resolution=0.1):
        dense_path = Path()
        dense_path.header = sparse_path.header

        if len(sparse_path.poses) < 2:
            return sparse_path

        for i in range(len(sparse_path.poses) - 1):
            p1 = sparse_path.poses[i].pose.position
            p2 = sparse_path.poses[i + 1].pose.position
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            distance = math.hypot(dx, dy)
            yaw = math.atan2(dy, dx)
            quat = self.get_quaternion_from_yaw(yaw)
            num_steps = max(1, int(distance / resolution))

            for j in range(num_steps):
                fraction = j / float(num_steps)
                step_pose = PoseStamped()
                step_pose.header = sparse_path.header
                step_pose.pose.position.x = p1.x + (dx * fraction)
                step_pose.pose.position.y = p1.y + (dy * fraction)
                step_pose.pose.orientation = quat
                dense_path.poses.append(step_pose)

        dense_path.poses.append(sparse_path.poses[-1])
        self.get_logger().info(
            f'Interpolated path: {len(sparse_path.poses)} -> {len(dense_path.poses)} poses'
        )
        return dense_path

    def path_callback(self, msg):
        self.get_logger().info(f'Received sparse path with {len(msg.poses)} poses')

        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error('Nav2 FollowPath action server not available')
            return

        dense_path = self.interpolate_path(msg)
        goal_msg = FollowPath.Goal()
        goal_msg.path = dense_path
        goal_msg.controller_id = 'FollowPath'

        self.get_logger().info('Sending dense path to Nav2 FollowPath')
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('FollowPath goal rejected by Nav2')
            return
        self.get_logger().info('FollowPath goal accepted by Nav2')


def main(args=None):
    rclpy.init(args=args)
    node = PathFollowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
