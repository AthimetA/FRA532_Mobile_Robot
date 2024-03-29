# Import libraries:
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration,Command, LaunchConfiguration, PythonExpression
from launch.actions import DeclareLaunchArgument
import xacro
import yaml
from nav2_common.launch import RewrittenYaml
    
# ========== **GENERATE LAUNCH DESCRIPTION** ========== #
def generate_launch_description():

    # Use sim time
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Test Node
    zhbbot_handler = Node(
        package='zhbbot_control',
        executable='zhbbot_handler.py',
        name='zhbbotHandlerNode',
    )

    zhbbot_vff = Node(
        package='zhbbot_control',
        executable='zhbbot_local_planer_vff_avoidance.py',
        name='ZhbbotVFFNode',
    )

    zhbbot_dwa = Node(
        package='zhbbot_control',
        executable='zhbbot_local_planer_dwa.py',
        name='ZhbbotDWANode',
    )

    # Inverse Kinematics Node
    zhbbot_inverse_kinemetic = Node(
        package='zhbbot_control',
        executable='zhbbot_inverse_kinemetic.py',
        name='ZhbbotIKNode',
    )

    # ***** RETURN LAUNCH DESCRIPTION ***** #
    return LaunchDescription([
        
        # Launch the test node
        zhbbot_handler,
        zhbbot_vff,
        zhbbot_dwa,
        zhbbot_inverse_kinemetic,

    ])