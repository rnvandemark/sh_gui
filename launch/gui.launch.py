from launch import LaunchDescription
from launch.actions import Shutdown
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from os.path import join as ojoin

def generate_launch_description():
    cfg = ojoin(
        get_package_share_directory("sh_gui"),
        "config",
        "params.yaml"
    )
    desc = LaunchDescription()
    desc.add_action(Node(
        package="sh_gui",
        executable="sh_gui",
        namespace="/smart_home",
        parameters=[cfg],
        on_exit=Shutdown(),
    ))
    return desc
