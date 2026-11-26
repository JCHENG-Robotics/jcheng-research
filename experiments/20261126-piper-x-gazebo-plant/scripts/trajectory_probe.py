#!/usr/bin/env python3
"""Send MVE-1 joint trajectories and measure the Piper X Gazebo plant.

The probe waits for the two trajectory action servers under ``/sim``, commands
the 6 arm joints and the master gripper joint, then reads ``/sim/piper_x/joint_states``
and reports:

* action status / error_code for both controllers;
* final position error per joint;
* whether the two mimic fingers satisfy q1 = +0.5*q_master and
  q2 = -0.5*q_master (an observation: some physics engines do not implement
  SDF mimic; see result.md).

The probe exits 0 only when both actions succeed and the tracking tolerances
are met. Mimic enforcement is reported but does not fail the run.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

DEFAULT_ARM_GOAL = {
    "joint1": 0.3,
    "joint2": 0.6,
    "joint3": -0.5,
    "joint4": 0.4,
    "joint5": -0.4,
    "joint6": 0.8,
}
ARM_TOLERANCE_RAD = 0.02
GRIPPER_TOLERANCE_M = 0.002
MIMIC_TOLERANCE_M = 1e-3
EXPECTED_JOINTS = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6",
    "gripper", "gripper_joint1", "gripper_joint2",
)


class Probe(Node):
    def __init__(self):
        super().__init__("mve1_piper_x_probe")
        self.latest: JointState | None = None
        self.create_subscription(JointState, "/sim/piper_x/joint_states", self._on_joint_state, 10)
        self.arm = ActionClient(
            self, FollowJointTrajectory, "/sim/piper_x/arm_controller/follow_joint_trajectory"
        )
        self.gripper = ActionClient(
            self, FollowJointTrajectory, "/sim/piper_x/gripper_controller/follow_joint_trajectory"
        )

    def _on_joint_state(self, message: JointState):
        self.latest = message

    def spin_until(self, predicate, timeout: float, period: float = 0.05) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=period)
            if predicate():
                return True
        return False

    def wait_for_server(self, client: ActionClient, name: str, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if client.wait_for_server(timeout_sec=1.0):
                return True
        raise RuntimeError(f"action server {name} not available after {timeout}s")

    def positions(self) -> dict[str, float]:
        if self.latest is None:
            return {}
        return dict(zip(self.latest.name, self.latest.position))

    def send_trajectory(
        self,
        client: ActionClient,
        joint_names: list[str],
        targets: dict[str, float],
        duration: float,
        timeout: float,
    ) -> dict:
        current = self.positions()
        missing = [name for name in joint_names if name not in current]
        if missing:
            raise RuntimeError(f"joint_states missing joints before goal: {missing}")

        goal = FollowJointTrajectory.Goal()
        trajectory = JointTrajectory()
        trajectory.joint_names = joint_names
        start = JointTrajectoryPoint()
        start.positions = [current[name] for name in joint_names]
        start.time_from_start.sec = 0
        end = JointTrajectoryPoint()
        end.positions = [targets[name] for name in joint_names]
        end.time_from_start.sec = int(duration)
        end.time_from_start.nanosec = int((duration % 1.0) * 1e9)
        trajectory.points = [start, end]
        goal.trajectory = trajectory

        started = time.monotonic()
        send_future = client.send_goal_async(goal)
        if not self.spin_until(send_future.done, timeout):
            raise RuntimeError("goal was not accepted within the timeout")
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            raise RuntimeError("goal rejected by the controller")
        result_future = goal_handle.get_result_async()
        if not self.spin_until(result_future.done, timeout):
            raise RuntimeError("action result did not arrive within the timeout")
        wrapper = result_future.result()
        elapsed = time.monotonic() - started
        result = wrapper.result
        return {
            "status": wrapper.status,
            "status_text": _status_text(wrapper.status),
            "error_code": int(result.error_code),
            "error_string": result.error_string,
            "elapsed_s": round(elapsed, 3),
        }

    def settle(self, targets: dict[str, float], tolerance: float, timeout: float) -> bool:
        def reached() -> bool:
            current = self.positions()
            if not all(name in current for name in targets):
                return False
            return all(abs(current[name] - value) <= tolerance for name, value in targets.items())

        return self.spin_until(reached, timeout)


def _status_text(status: int) -> str:
    return {
        0: "UNKNOWN",
        1: "ACCEPTED",
        2: "EXECUTING",
        3: "CANCELING",
        4: "SUCCEEDED",
        5: "CANCELED",
        6: "ABORTED",
    }.get(status, f"STATUS_{status}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-goal", default=json.dumps(DEFAULT_ARM_GOAL))
    parser.add_argument("--gripper-goal", type=float, default=0.08)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--state-timeout", type=float, default=20.0)
    parser.add_argument("--action-timeout", type=float, default=30.0)
    parser.add_argument("--settle-timeout", type=float, default=10.0)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    arm_goal = json.loads(args.arm_goal)
    if set(arm_goal) != set(DEFAULT_ARM_GOAL):
        parser.error(f"--arm-goal must name exactly {sorted(DEFAULT_ARM_GOAL)}")

    rclpy.init()
    node = Probe()
    report: dict = {
        "schema": "jcheng.piper_x_mve1_runtime.v1",
        "arm_goal": arm_goal,
        "gripper_goal": args.gripper_goal,
        "duration_s": args.duration,
        "tolerances": {
            "arm_rad": ARM_TOLERANCE_RAD,
            "gripper_m": GRIPPER_TOLERANCE_M,
            "mimic_m": MIMIC_TOLERANCE_M,
        },
        "errors": [],
    }
    exit_code = 1
    try:
        if not node.spin_until(lambda: node.latest is not None, args.state_timeout):
            raise RuntimeError("/sim/piper_x/joint_states did not arrive")
        initial = node.positions()
        report["joint_names"] = list(node.latest.name)
        report["missing_expected_joints"] = [
            name for name in EXPECTED_JOINTS if name not in initial
        ]
        report["initial"] = {name: round(initial[name], 6) for name in sorted(initial)}

        required = list(DEFAULT_ARM_GOAL) + ["gripper"]
        missing_required = [name for name in required if name not in initial]
        if missing_required:
            raise RuntimeError(f"joint_states missing commanded joints: {missing_required}")

        node.wait_for_server(node.arm, "arm_controller", args.action_timeout)
        node.wait_for_server(node.gripper, "gripper_controller", args.action_timeout)

        report["arm"] = node.send_trajectory(
            node.arm,
            list(DEFAULT_ARM_GOAL),
            arm_goal,
            args.duration,
            args.action_timeout + args.duration,
        )
        report["gripper"] = node.send_trajectory(
            node.gripper,
            ["gripper"],
            {"gripper": args.gripper_goal},
            args.duration,
            args.action_timeout + args.duration,
        )

        node.settle(arm_goal, ARM_TOLERANCE_RAD, args.settle_timeout)
        node.settle({"gripper": args.gripper_goal}, GRIPPER_TOLERANCE_M, args.settle_timeout)
        final = node.positions()
        report["final"] = {name: round(final[name], 6) for name in sorted(final)}

        arm_errors = {
            name: round(final[name] - value, 6)
            for name, value in arm_goal.items()
            if name in final
        }
        report["arm_errors_rad"] = arm_errors
        report["arm_max_abs_error_rad"] = round(
            max((abs(value) for value in arm_errors.values()), default=math.inf), 6
        )

        gripper_error = final["gripper"] - args.gripper_goal
        report["gripper_error_m"] = round(gripper_error, 6)
        report["gripper_travel_m"] = round(final["gripper"] - initial["gripper"], 6)

        master = final["gripper"]
        mimic = {}
        for name, multiplier in (("gripper_joint1", 0.5), ("gripper_joint2", -0.5)):
            if name not in final:
                mimic[name] = {"present": False, "multiplier": multiplier}
                continue
            expected = multiplier * master
            mimic[name] = {
                "present": True,
                "expected_m": round(expected, 6),
                "actual_m": round(final[name], 6),
                "delta_m": round(final[name] - expected, 6),
                "multiplier": multiplier,
            }
        report["mimic"] = mimic
        report["mimic_enforced"] = all(
            item.get("present") and abs(item["delta_m"]) <= MIMIC_TOLERANCE_M
            for item in mimic.values()
        )

        actions_ok = (
            report["arm"]["status"] == 4
            and report["arm"]["error_code"] == 0
            and report["gripper"]["status"] == 4
            and report["gripper"]["error_code"] == 0
        )
        tracking_ok = (
            report["arm_max_abs_error_rad"] <= ARM_TOLERANCE_RAD
            and abs(gripper_error) <= GRIPPER_TOLERANCE_M
        )
        report["pass"] = {
            "actions": actions_ok,
            "tracking": tracking_ok,
            "mimic_enforced": report["mimic_enforced"],
        }
        exit_code = 0 if actions_ok and tracking_ok else 2
    except Exception as exc:  # noqa: BLE001 - report every failure in the JSON
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.shutdown()

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
