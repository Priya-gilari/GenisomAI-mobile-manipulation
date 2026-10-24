#!/usr/bin/env python3
"""Turn Gazebo ground truth into odometry: TF odom->BASE_LINK and /odom topic."""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class GroundTruthOdom(Node):
    def __init__(self):
        super().__init__('gt_odom')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.create_subscription(Odometry, 'ground_truth', self.callback, 10)

    def callback(self, msg):
        # 1) TF odom -> BASE_LINK
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'BASE_LINK'
        p = msg.pose.pose
        t.transform.translation.x = p.position.x
        t.transform.translation.y = p.position.y
        t.transform.translation.z = p.position.z
        t.transform.rotation = p.orientation
        self.tf_broadcaster.sendTransform(t)

        # 2) /odom topic (Nav2 reads this)
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'BASE_LINK'
        self.odom_pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(GroundTruthOdom())


if __name__ == '__main__':
    main()
