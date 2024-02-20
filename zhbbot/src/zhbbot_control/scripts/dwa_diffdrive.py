import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav2_msgs.action import ComputePathToPose
from geometry_msgs.msg import PoseStamped, Twist, Point
import tf_transformations
import math
import tf2_ros
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from geometry_msgs.msg import Pose, TransformStamped
from nav_msgs.msg import Odometry
import numpy as np
from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA

from zhbbot_interfaces.srv import RobotSentgoal, Goalreach

class DynamicWindowApproach(Node):
    # Constructor of the class
    def __init__(self):
        # Initialize the ROS 2 node
        super().__init__('dynamic_window_approach')

        # Create a subscription to the laser scan topic
        self.create_subscription(LaserScan, "/scan", self.laser_scan_callback, 10)
        # Variable to store the latest laser scan data
        self.laser_scan = None

        # Create a subscription for the current pose of the robot
        self.odom_buffer = Odometry()
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Create a timer to control the control loop
        self.timer_callback_loop = self.create_timer(1/10, self.timer_callback)

        # Create a publisher for robot velocity commands
        self.velocity_publisher = self.create_publisher(Twist, '/cmd_vel_zhbbot', 10) # publish to /cmd_vel_zhbbot topic

        self.min_speed = 0.0
        self.max_speed = 0.5
        self.min_rot_speed = -3.0
        self.max_rot_speed = 3.0
        self.goal = [9,-3]

    # Timer callback for the control loop
    def timer_callback(self):
        # Get the best velocity command
        best_velocity = self.select_best_trajectory(self.goal)

        msg = Twist()
        msg.linear.x = best_velocity[0]
        msg.angular.z = best_velocity[1]
        self.velocity_publisher.publish(msg)
        
    # Callback for processing laser scan messages
    def laser_scan_callback(self, msg):
        # Store the laser scan data for use in the controller
        self.laser_scan = msg

    # Callback for processing odometry messages
    def odom_callback(self, msg):
        # Store the odometry data for use in the controller
        self.odom_buffer = msg

    def score_trajectory(self, new_x, new_y, goal):
        distance_diff = math.sqrt((goal[0]-new_x)**2 + (goal[1]-new_y)**2)
        obstacle_diff = self.obstacle_diff(new_x, new_y)
        return -distance_diff + obstacle_diff
    
    def obstacle_diff(self, new_x, new_y):
        obstacle_diff = 0
        obstacle_max_distance = 1
        nearest_obstacle_angle = np.argmin(self.laser_scan.ranges)
        dist_nearest = self.laser_scan.ranges[nearest_obstacle_angle]
        if dist_nearest < obstacle_max_distance:
            obstacle_angle = self.laser_scan.angle_min + (self.laser_scan.angle_increment * nearest_obstacle_angle)
            obstacle_x = self.laser_scan.ranges[nearest_obstacle_angle] * math.cos(obstacle_angle)
            obstacle_y = self.laser_scan.ranges[nearest_obstacle_angle] * math.sin(obstacle_angle)
            obstacle_diff = math.sqrt((obstacle_x-new_x)**2 + (obstacle_y-new_y)**2)

            return obstacle_diff
        else:
            return 1

    def select_best_trajectory(self, goal):
        x = self.odom_buffer.pose.pose.position.x
        y = self.odom_buffer.pose.pose.position.y
        quaternion = (self.odom_buffer.pose.pose.orientation.x, 
                      self.odom_buffer.pose.pose.orientation.y, 
                      self.odom_buffer.pose.pose.orientation.z, 
                      self.odom_buffer.pose.pose.orientation.w)
        
        theta = tf_transformations.euler_from_quaternion(quaternion)[2]

        goal_radius = 0.5

        current_score = float('-inf')

        goal_distance = math.sqrt((goal[0]-x)**2 + (goal[1]-y)**2)

        while goal_distance > goal_radius:
            for linear_speed in np.arange(self.min_speed, self.max_speed, 0.1):
                for rot_speed in np.arange(self.min_rot_speed, self.max_rot_speed, 0.1):
                    # Simulate trajectory
                    new_x = x + linear_speed * math.cos(rot_speed)
                    new_y = y + linear_speed * math.sin(rot_speed)

                    # Score trajectory
                    score = self.score_trajectory(new_x, new_y, goal)
                    if score > current_score:
                        current_score = score
                        best_velocity = [linear_speed, rot_speed]
                        self.get_logger().info('Best velocity: ' + str(best_velocity))
    
            return best_velocity
        return [0.0, 0.0]

# Main function to initialize and run the ROS 2 node
def main(args=None):
    rclpy.init(args=args)
    node = DynamicWindowApproach()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()