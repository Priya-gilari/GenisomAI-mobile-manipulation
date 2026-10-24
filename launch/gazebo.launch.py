import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (IncludeLaunchDescription, RegisterEventHandler,
                            ExecuteProcess, AppendEnvironmentVariable, TimerAction)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('zsl1w_description')
    robot_description = xacro.process_file(
        os.path.join(pkg, 'urdf', 'zsl1w_gazebo.urdf.xacro')).toxml()

    model_path = AppendEnvironmentVariable('GAZEBO_MODEL_PATH', os.path.dirname(pkg))

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': os.path.join(pkg, 'worlds', 'flat.world')}.items())

    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher',
               parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
               output='screen')

    # spawn at standing height (wheel centre 0.288 m below hip + wheel radius 0.070 m)
    spawn = Node(package='gazebo_ros', executable='spawn_entity.py',
                 arguments=['-topic', 'robot_description', '-entity', 'zsl1w', '-x', '-3.5', '-y', '-0.5', '-z', '0.37'],
                 output='screen')

    def spawner(name):
        return Node(package='controller_manager', executable='spawner', arguments=[name])

    legs = spawner('leg_controller')
    jsb = spawner('joint_state_broadcaster')
    wheels = spawner('diff_drive_controller')

    joints = ['FBL_ABAD_JOINT', 'FBL_HIP_JOINT', 'FBL_KNEE_JOINT',
              'FAR_ABAD_JOINT', 'FAR_HIP_JOINT', 'FAR_KNEE_JOINT',
              'RAR_ABAD_JOINT', 'RAR_HIP_JOINT', 'RAR_KNEE_JOINT',
              'RBL_ABAD_JOINT', 'RBL_HIP_JOINT', 'RBL_KNEE_JOINT']
    pose = [0.0, 0.8, -1.6] * 4
    msg = ('{joint_names: [' + ', '.join(joints) + '], '
           'points: [{positions: [' + ', '.join(str(p) for p in pose) + '], '
           'time_from_start: {sec: 2}}]}')
    stand = ExecuteProcess(cmd=['ros2', 'topic', 'pub', '--once', '/leg_controller/joint_trajectory',
                                'trajectory_msgs/msg/JointTrajectory', msg],
                           output='screen')

    return LaunchDescription([
        model_path, gazebo, rsp, spawn,
        # 1) right after spawning: leg motors first, then joint states
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[legs, jsb])),
        # 2) leg controller active -> stand up (2 s)
        RegisterEventHandler(OnProcessExit(target_action=legs, on_exit=[stand])),
        # 3) 3 s after the stand command -> enable wheels
        RegisterEventHandler(OnProcessExit(target_action=stand,
                                           on_exit=[TimerAction(period=3.0, actions=[wheels])])),
    ])
