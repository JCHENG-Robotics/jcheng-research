"""Gazebo Harmonic bring-up for the MVE-1 Piper X plant, confined to domain 43.

This is an experiment launch file, not a product bring-up. It generates the
plant URDF from the pinned MIT source with ``plant/piper_x_plant.py``, spawns
it in a self-contained world, then activates, in order, the joint state
broadcaster and the arm and gripper trajectory controllers. A stage starts only
if the previous process exited 0, and every stage has its own 60 s wall
deadline. ``robot_state_publisher`` or ``/clock`` bridge exit, or a missed
deadline, shuts the whole launch down.

Every ROS name lives under ``/sim`` or is bridged from Gazebo. The launch
rejects any ``ROS_DOMAIN_ID`` other than 43 and sets
``GZ_PARTITION=jcheng-sim``.
"""

import os
import sys
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

PLANT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PLANT_DIR))

from piper_x_plant import PlantBuildError, build_plant  # noqa: E402

CONTROLLER_MANAGER = "/sim/piper_x/controller_manager"
STAGE_TIMEOUT_SECONDS = 60.0
SPAWN_DELAY_SECONDS = 3.0


def _validate_domain(context) -> list:
    domain = LaunchConfiguration("domain_id").perform(context).strip()
    if domain != "43":
        raise RuntimeError(
            "the Piper X simulation plant is confined to ROS_DOMAIN_ID=43; "
            f"received domain_id:={domain!r}"
        )
    return []


def _shutdown(stage, reason):
    return [
        LogInfo(msg=f"Piper X plant launch failure: stage={stage}; {reason}"),
        EmitEvent(event=Shutdown(reason=f"{stage}: {reason}")),
    ]


def _start_stage(stage, action):
    return [action, _watchdog(stage)]


def _after_success(stage, next_stage=None):
    def callback(event, context):
        if event.returncode == 0:
            context.launch_configurations[f"piper_startup_{stage}_completed"] = "true"
            return _start_stage(*next_stage) if next_stage else []
        return _shutdown(
            stage, f"command={event.process_name}; returncode={event.returncode}"
        )

    return callback


def _watchdog(stage):
    def callback(context):
        if context.launch_configurations.get(f"piper_startup_{stage}_completed") == "true":
            return []
        return _shutdown(stage, f"wall deadline exceeded ({STAGE_TIMEOUT_SECONDS}s)")

    return TimerAction(
        period=STAGE_TIMEOUT_SECONDS,
        actions=[OpaqueFunction(function=callback)],
    )


def _launch_setup(context, *unused):
    asset_root = LaunchConfiguration("asset_root").perform(context).strip() or None
    joint_map = LaunchConfiguration("joint_map").perform(context)
    controllers = LaunchConfiguration("controllers").perform(context)
    urdf_out = Path(LaunchConfiguration("urdf_out").perform(context))
    world = LaunchConfiguration("world").perform(context)
    model_name = LaunchConfiguration("model_name").perform(context)
    headless = LaunchConfiguration("headless").perform(context).strip().lower()
    headless = headless in ("1", "true", "yes")
    mimic_interfaces = (
        LaunchConfiguration("mimic_state_interfaces").perform(context).strip().lower()
        in ("1", "true", "yes")
    )

    try:
        build = build_plant(
            joint_map_path=joint_map,
            asset_root=asset_root,
            controllers_yaml=controllers,
            model_name=model_name,
            include_mimic_interfaces=mimic_interfaces,
        )
    except (PlantBuildError, OSError) as exc:
        raise RuntimeError(f"Piper X plant launch failure: stage=plant_build; {exc}") from exc

    urdf_out.parent.mkdir(parents=True, exist_ok=True)
    urdf_out.write_text(build.urdf_text, encoding="utf-8")

    server_flag = "-s" if headless else ""
    rendering_flag = ""  # server-only: no sensors, no rendering needed
    gz_args = f"-r {server_flag} {rendering_flag} -v 3 {world}"

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace="/sim/piper_x",
        output="screen",
        parameters=[
            {
                "robot_description": ParameterValue(build.urdf_text, value_type=str),
                "use_sim_time": True,
            }
        ],
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ),
        launch_arguments={"gz_args": gz_args, "on_exit_shutdown": "true"}.items(),
    )
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        namespace="/sim/piper_x",
        arguments=[
            "-topic", "/sim/piper_x/robot_description",
            "-name", model_name,
            "-z", "0.0",
        ],
        output="screen",
    )
    common_spawner_args = [
        "-c",
        CONTROLLER_MANAGER,
        "--controller-manager-timeout",
        "55",
        "--switch-timeout",
        "55",
        "--service-call-timeout",
        "55",
    ]
    jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", *common_spawner_args],
        output="screen",
    )
    arm = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", *common_spawner_args],
        output="screen",
    )
    gripper = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", *common_spawner_args],
        output="screen",
    )

    return [
        RegisterEventHandler(
            OnProcessExit(target_action=spawn, on_exit=_after_success("spawn", ("jsb", jsb)))
        ),
        RegisterEventHandler(
            OnProcessExit(target_action=jsb, on_exit=_after_success("jsb", ("arm", arm)))
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=arm,
                on_exit=_after_success("arm", ("gripper", gripper)),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=gripper, on_exit=_after_success("gripper", None)
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=robot_state_publisher,
                on_exit=lambda event, context: _shutdown(
                    "robot_state_publisher", f"returncode={event.returncode}"
                ),
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=clock_bridge,
                on_exit=lambda event, context: _shutdown(
                    "clock_bridge", f"returncode={event.returncode}"
                ),
            )
        ),
        _watchdog("spawn"),
        gazebo,
        robot_state_publisher,
        TimerAction(period=SPAWN_DELAY_SECONDS, actions=[spawn, clock_bridge]),
        LogInfo(
            msg=(
                "Piper X plant built: "
                f"commit={build.report['source']['commit'][:8]} "
                f"links={build.report['counts']['links']} "
                f"joints={build.report['counts']['joints']} "
                f"movable={build.report['counts']['movable']} "
                f"mass_kg={build.report['total_mass_kg']} "
                f"mesh_refs={build.report['meshes']['references']} "
                f"adaptations={[a['id'] for a in build.report['adaptations']]} "
                f"urdf_out={urdf_out} world={world} headless={headless} namespace=/sim/piper_x"
            )
        ),
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "domain_id",
                default_value="43",
                description="ROS domain; only 43 is accepted",
            ),
            DeclareLaunchArgument(
                "asset_root",
                default_value="",
                description=(
                    "Asset bundle root containing agx_arm_urdf-<commit>; empty "
                    "uses JCHENG_ASSET_ROOT or ~/.local/share/jcheng/assets/piper_x"
                ),
            ),
            DeclareLaunchArgument(
                "joint_map",
                default_value=str(
                    WORKSPACE_ROOT
                    / "jcheng-simulation"
                    / "docs"
                    / "robots"
                    / "piper_x"
                    / "joint_map.yaml"
                ),
                description="Checked-in Piper X joint contract",
            ),
            DeclareLaunchArgument(
                "controllers",
                default_value=str(PLANT_DIR / "config" / "piper_x_controllers.yaml"),
                description="ros2_control controller configuration",
            ),
            DeclareLaunchArgument(
                "urdf_out",
                default_value=str(PLANT_DIR.parent / "generated" / "piper_x_gazebo.urdf"),
                description="Where the generated plant URDF is written",
            ),
            DeclareLaunchArgument(
                "world",
                default_value=str(PLANT_DIR / "worlds" / "piper_x_lab.sdf"),
                description="Self-contained Gazebo world",
            ),
            DeclareLaunchArgument(
                "model_name",
                default_value="piper_x",
                description="Spawned Gazebo model name",
            ),
            DeclareLaunchArgument(
                "headless",
                default_value="true",
                description="Run Gazebo with the server only",
            ),
            DeclareLaunchArgument(
                "mimic_state_interfaces",
                default_value="true",
                description="Export state interfaces for the two mimic finger joints",
            ),
            SetEnvironmentVariable("ROS_DOMAIN_ID", LaunchConfiguration("domain_id")),
            SetEnvironmentVariable("GZ_PARTITION", "jcheng-sim"),
            OpaqueFunction(function=_validate_domain),
            OpaqueFunction(function=_launch_setup),
        ]
    )
