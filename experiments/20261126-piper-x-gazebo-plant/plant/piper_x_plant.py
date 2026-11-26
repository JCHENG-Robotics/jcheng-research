#!/usr/bin/env python3
"""Build a Gazebo Harmonic plant from the pinned MIT Piper X description.

The MIT ``agx_arm_urdf@680fa925`` files are the only geometry, inertia and
joint-axis authority. This module:

* verifies the two source SHA-256 values against the checked-in joint map;
* composes ``piper_x_description.urdf`` with the AGX gripper body from
  ``piper_x_with_gripper_description.xacro`` (the xacro body is parsed as XML;
  its ``xacro:include`` is skipped because the arm URDF is composed directly);
* overwrites every movable joint limit with the value in ``joint_map.yaml``;
* rewrites ``package://agx_arm_description/agx_arm_urdf/...`` mesh URIs to
  ``file://`` paths inside the external asset bundle;
* adds the one simulation-only adaptation the conversion needs (a placeholder
  inertial on the massless ``gripper_link``; without it ``urdf2sdf`` drops the
  master gripper joint);
* appends the ``gz_ros2_control`` plugin and ``<ros2_control>`` blocks in the
  ``/sim/piper_x`` namespace.

Every deviation from the source is recorded in the returned report. Nothing is
edited silently, and the source files are only read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import yaml

XACRO_NS = "{http://www.ros.org/wiki/xacro}"
MESH_PACKAGE_PREFIX = "package://agx_arm_description/agx_arm_urdf/"
ASSET_DIR_PREFIX = "agx_arm_urdf-"
DEFAULT_ASSET_ROOT = Path.home() / ".local/share/jcheng/assets/piper_x"
DEFAULT_JOINT_MAP = (
    Path(__file__).resolve().parents[4]
    / "jcheng-simulation"
    / "docs"
    / "robots"
    / "piper_x"
    / "joint_map.yaml"
)
ARM_URDF_REL = "piper_x/urdf/piper_x_description.urdf"
GRIPPER_XACRO_REL = "piper_x/urdf/piper_x_with_gripper_description.xacro"

EXPECTED_SHA256 = {
    ARM_URDF_REL: "93eb2a84d01df81566a3c1ed275626d93a1c4275564a30c7899a35a672e265bb",
    GRIPPER_XACRO_REL: "88561fe45a3f4e639c7a233b13574d88d7707b545110cb30b983e360cdb57420",
}

# Simulation-only placeholder for the massless virtual link. These are not
# measured values; they only keep urdf2sdf from dropping the gripper joint.
GRIPPER_LINK_PLACEHOLDER = {
    "mass": 0.05,
    "inertia": {"ixx": 1.0e-4, "ixy": 0.0, "ixz": 0.0,
                "iyy": 1.0e-4, "iyz": 0.0, "izz": 1.0e-4},
}

ACTUATED_JOINTS = ("joint1", "joint2", "joint3", "joint4", "joint5",
                   "joint6", "gripper")
MIMIC_JOINTS = ("gripper_joint1", "gripper_joint2")


class PlantBuildError(RuntimeError):
    """Raised when the pinned source or the joint contract cannot be honoured."""


@dataclass
class PlantBuild:
    urdf_text: str
    report: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_asset_dir(asset_root: str | os.PathLike[str] | None = None) -> Path:
    """Return the single ``agx_arm_urdf-<commit>`` directory under the root."""
    if asset_root:
        root = Path(asset_root).expanduser()
    else:
        root = Path(
            os.environ.get("JCHENG_ASSET_ROOT", str(DEFAULT_ASSET_ROOT))
        ).expanduser()
    if not root.is_dir():
        raise PlantBuildError(
            f"asset root not found: {root}; run "
            "jcheng-simulation/scripts/fetch_piper_x_assets.sh first"
        )
    candidates = sorted(
        path for path in root.iterdir()
        if path.is_dir() and path.name.startswith(ASSET_DIR_PREFIX)
    )
    if len(candidates) != 1:
        raise PlantBuildError(
            f"expected exactly one {ASSET_DIR_PREFIX}* directory under {root}, "
            f"found: {[path.name for path in candidates]}"
        )
    return candidates[0]


def load_joint_map(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data.get("schema") != "jcheng.piper_x_joint_map.v1":
        raise PlantBuildError(
            f"unexpected joint map schema: {data.get('schema')!r} ({path})"
        )
    return data


def flatten_joint_map(joint_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    flat: dict[str, dict[str, Any]] = {
        joint["name"]: joint for joint in joint_map["joints"]
    }
    for key in ("flange", "gripper_base", "master"):
        entry = joint_map["end_effector"][key]
        flat[entry["name"]] = entry
    for entry in joint_map["end_effector"]["mimic"]:
        flat[entry["name"]] = entry
    return flat


def _fmt(value: float) -> str:
    return f"{float(value):.12g}"


def _limit_keys(joint_type: str) -> tuple[str, str, str, str]:
    if joint_type == "revolute":
        return "lower_rad", "upper_rad", "velocity_rad_s", "effort_nm"
    if joint_type == "prismatic":
        return "lower_m", "upper_m", "velocity_m_s", "effort_n"
    raise PlantBuildError(f"unsupported movable joint type: {joint_type!r}")


def _parse_source(asset_dir: Path, joint_map: dict[str, Any]) -> dict[str, Any]:
    hashes = {}
    for rel, expected in EXPECTED_SHA256.items():
        path = asset_dir / rel
        if not path.is_file():
            raise PlantBuildError(f"pinned source missing: {path}")
        actual = sha256_file(path)
        hashes[rel] = {"sha256": actual, "expected": expected, "match": actual == expected}
        if actual != expected:
            raise PlantBuildError(
                f"pinned source hash mismatch for {rel}: {actual} != {expected}"
            )
        map_expected = joint_map["source"].get(
            "urdf_sha256" if rel == ARM_URDF_REL else "gripper_xacro_sha256"
        )
        if map_expected and actual != map_expected:
            raise PlantBuildError(
                f"{rel} does not match joint_map.yaml source hash: "
                f"{actual} != {map_expected}"
            )
    declared_commit = joint_map["source"]["commit"]
    if not asset_dir.name.endswith(declared_commit[:8]):
        raise PlantBuildError(
            f"asset directory {asset_dir.name!r} does not carry commit "
            f"{declared_commit[:8]}"
        )
    return {"commit": declared_commit, "asset_dir": str(asset_dir), "files": hashes}


def _compose_root(asset_dir: Path) -> ET.Element:
    arm_root = ET.parse(asset_dir / ARM_URDF_REL).getroot()
    xacro_root = ET.parse(asset_dir / GRIPPER_XACRO_REL).getroot()
    existing = {link.get("name") for link in arm_root.findall("link")}
    for element in list(xacro_root):
        if element.tag.startswith(XACRO_NS):
            continue
        if element.tag == "link":
            name = element.get("name")
            if name in existing:
                raise PlantBuildError(
                    f"gripper xacro link {name!r} duplicates an arm link"
                )
            existing.add(name)
        arm_root.append(element)
    return arm_root


def _apply_limits(
    root: ET.Element, flat: dict[str, dict[str, Any]], report: dict[str, Any]
) -> None:
    for joint in root.findall("joint"):
        name = joint.get("name")
        joint_type = joint.get("type")
        entry = flat.get(name)
        if entry is None:
            raise PlantBuildError(f"joint {name!r} is not in joint_map.yaml")
        if entry.get("type") != joint_type:
            raise PlantBuildError(
                f"joint {name!r} type {joint_type!r} != joint_map "
                f"{entry.get('type')!r}"
            )
        record: dict[str, Any] = {
            "name": name,
            "type": joint_type,
            "parent": joint.find("parent").get("link"),
            "child": joint.find("child").get("link"),
        }
        axis_el = joint.find("axis")
        if axis_el is not None:
            record["axis"] = [float(v) for v in axis_el.get("xyz").split()]
        if joint_type == "fixed":
            record["limits"] = None
            report["joints"].append(record)
            continue

        lower_key, upper_key, velocity_key, effort_key = _limit_keys(joint_type)
        limit = joint.find("limit")
        if limit is None:
            limit = ET.SubElement(joint, "limit")
        before = {key: limit.get(key) for key in ("lower", "upper", "effort", "velocity")}
        limit.set("lower", _fmt(entry[lower_key]))
        limit.set("upper", _fmt(entry[upper_key]))
        limit.set("effort", _fmt(entry[effort_key]))
        limit.set("velocity", _fmt(entry[velocity_key]))
        after = {key: limit.get(key) for key in ("lower", "upper", "effort", "velocity")}
        deltas = {}
        for key in ("lower", "upper", "effort", "velocity"):
            if before[key] is None:
                deltas[key] = None
                continue
            deltas[key] = abs(float(before[key]) - float(after[key]))
            if deltas[key] > 1e-9:
                raise PlantBuildError(
                    f"joint {name!r} limit {key} differs from joint_map: "
                    f"{before[key]} -> {after[key]}"
                )
        record["limits"] = {
            "lower": float(after["lower"]),
            "upper": float(after["upper"]),
            "effort": float(after["effort"]),
            "velocity": float(after["velocity"]),
        }
        record["source_limit_delta"] = deltas

        if entry.get("axis") is not None:
            map_axis = [float(v) for v in entry["axis"]]
            record["map_axis"] = map_axis
            record["axis_matches_map"] = record.get("axis") == map_axis

        mimic = joint.find("mimic")
        if mimic is not None:
            record["mimic"] = {
                "joint": mimic.get("joint"),
                "multiplier": float(mimic.get("multiplier", "1")),
                "offset": float(mimic.get("offset", "0")),
            }
            map_mimic = entry.get("mimic")
            if not isinstance(map_mimic, dict):
                raise PlantBuildError(
                    f"joint {name!r} has <mimic> but joint_map has no mimic entry"
                )
            if (
                record["mimic"]["joint"] != map_mimic["joint"]
                or abs(record["mimic"]["multiplier"] - map_mimic["multiplier"]) > 1e-12
                or abs(record["mimic"]["offset"] - map_mimic["offset"]) > 1e-12
            ):
                raise PlantBuildError(
                    f"joint {name!r} mimic {record['mimic']} != joint_map "
                    f"{map_mimic}"
                )
        report["joints"].append(record)


def _add_placeholder_inertial(root: ET.Element, report: dict[str, Any]) -> None:
    for link in root.findall("link"):
        if link.get("name") != "gripper_link":
            continue
        if link.find("inertial") is not None:
            return
        inertial = ET.SubElement(link, "inertial")
        ET.SubElement(inertial, "origin", {"xyz": "0 0 0", "rpy": "0 0 0"})
        ET.SubElement(inertial, "mass", {"value": _fmt(GRIPPER_LINK_PLACEHOLDER["mass"])})
        ET.SubElement(
            inertial,
            "inertia",
            {key: _fmt(value) for key, value in GRIPPER_LINK_PLACEHOLDER["inertia"].items()},
        )
        report["adaptations"].append(
            {
                "id": "gripper_link_placeholder_inertial",
                "reason": (
                    "the MIT xacro declares gripper_link without <inertial>; "
                    "urdf2sdf drops massless links and with them the master "
                    "'gripper' joint, which also breaks the mimic references"
                ),
                "values": GRIPPER_LINK_PLACEHOLDER,
                "status": "simulation placeholder, not a measured value",
            }
        )
        return
    raise PlantBuildError("gripper_link not found in the composed URDF")


def _rewrite_meshes(
    root: ET.Element, asset_dir: Path, report: dict[str, Any]
) -> None:
    seen = set()
    for link in root.findall("link"):
        link_name = link.get("name")
        for kind in ("visual", "collision"):
            for holder in link.findall(kind):
                mesh = holder.find("geometry/mesh")
                if mesh is None:
                    continue
                filename = mesh.get("filename", "")
                if not filename.startswith(MESH_PACKAGE_PREFIX):
                    raise PlantBuildError(
                        f"{link_name}/{kind}: unexpected mesh URI {filename!r}"
                    )
                relative = filename[len(MESH_PACKAGE_PREFIX):]
                path = asset_dir / relative
                exists = path.is_file()
                report["meshes"]["items"].append(
                    {
                        "link": link_name,
                        "kind": kind,
                        "source_uri": filename,
                        "relative_path": relative,
                        "resolved": str(path),
                        "exists": exists,
                        "bytes": path.stat().st_size if exists else 0,
                    }
                )
                if not exists:
                    report["meshes"]["missing"].append(str(path))
                    raise PlantBuildError(f"mesh missing: {path}")
                mesh.set("filename", path.as_uri())
                seen.add(str(path))
    report["meshes"]["references"] = len(report["meshes"]["items"])
    report["meshes"]["unique_files"] = len(seen)
    report["meshes"]["total_bytes"] = sum(
        item["bytes"] for item in report["meshes"]["items"]
    )


def _add_control_blocks(
    root: ET.Element,
    controllers_yaml: Path,
    report: dict[str, Any],
    include_mimic_interfaces: bool = True,
) -> None:
    gazebo = ET.SubElement(root, "gazebo")
    plugin = ET.SubElement(
        gazebo,
        "plugin",
        {
            "filename": "libgz_ros2_control-system.so",
            "name": "gz_ros2_control::GazeboSimROS2ControlPlugin",
        },
    )
    ros = ET.SubElement(plugin, "ros")
    ET.SubElement(ros, "namespace").text = "/sim/piper_x"
    ET.SubElement(ros, "remapping").text = "/robot_description:=/sim/piper_x/robot_description"
    ET.SubElement(ros, "remapping").text = "robot_description:=/sim/piper_x/robot_description"
    ET.SubElement(plugin, "parameters").text = str(controllers_yaml)
    report["adaptations"].append(
        {
            "id": "gz_ros2_control_plugin",
            "reason": (
                "run the controller manager inside Gazebo in the /sim/piper_x "
                "namespace and remap robot_description to the namespaced "
                "topic published by robot_state_publisher"
            ),
            "controllers_yaml": str(controllers_yaml),
        }
    )

    block = ET.SubElement(root, "ros2_control", {"name": "PiperXSystem", "type": "system"})
    hardware = ET.SubElement(block, "hardware")
    ET.SubElement(hardware, "plugin").text = "gz_ros2_control/GazeboSimSystem"

    limits = {record["name"]: record["limits"] for record in report["joints"]}
    for name in ACTUATED_JOINTS:
        joint = ET.SubElement(block, "joint", {"name": name})
        ET.SubElement(joint, "command_interface", {"name": "position"})
        ET.SubElement(joint, "state_interface", {"name": "position"})
        ET.SubElement(joint, "state_interface", {"name": "velocity"})
    if include_mimic_interfaces:
        for name in MIMIC_JOINTS:
            joint = ET.SubElement(block, "joint", {"name": name})
            ET.SubElement(joint, "state_interface", {"name": "position"})
            ET.SubElement(joint, "state_interface", {"name": "velocity"})
    report["adaptations"].append(
        {
            "id": "ros2_control_system",
            "reason": (
                "expose position commands for the 6 arm joints and the master "
                "gripper joint, and position/velocity state for all 9 movable "
                "joints including the two mimic fingers"
            ),
            "actuated": list(ACTUATED_JOINTS),
            "mimic": list(MIMIC_JOINTS),
        }
    )


def build_plant(
    joint_map_path: str | os.PathLike[str] = DEFAULT_JOINT_MAP,
    asset_root: str | os.PathLike[str] | None = None,
    controllers_yaml: str | os.PathLike[str] | None = None,
    model_name: str = "piper_x",
    include_mimic_interfaces: bool = True,
) -> PlantBuild:
    joint_map_path = Path(joint_map_path).expanduser().resolve()
    joint_map = load_joint_map(joint_map_path)
    asset_dir = locate_asset_dir(asset_root)
    controllers = Path(controllers_yaml or (Path(__file__).parent / "config/piper_x_controllers.yaml"))
    controllers = controllers.expanduser().resolve()
    if not controllers.is_file():
        raise PlantBuildError(f"controller config not found: {controllers}")

    report: dict[str, Any] = {
        "schema": "jcheng.piper_x_gazebo_plant.v1",
        "generated": date.today().isoformat(),
        "model_name": model_name,
        "source": _parse_source(asset_dir, joint_map),
        "joint_map": str(joint_map_path),
        "meshes": {"items": [], "missing": []},
        "adaptations": [
            {
                "id": "mesh_uri_rewrite",
                "reason": (
                    "Gazebo cannot resolve package://agx_arm_description; "
                    "resolve every mesh inside the external MIT asset bundle"
                ),
                "from": MESH_PACKAGE_PREFIX,
                "to": f"file://{asset_dir}/",
            },
            {
                "id": "joint_limits_from_joint_map",
                "reason": (
                    "joint_map.yaml is the checked-in limit contract; every "
                    "movable joint limit is rewritten from it and the source "
                    "delta is asserted to be zero"
                ),
            },
        ],
        "joints": [],
    }

    root = _compose_root(asset_dir)
    root.set("name", model_name)
    _apply_limits(root, flatten_joint_map(joint_map), report)
    _add_placeholder_inertial(root, report)
    _rewrite_meshes(root, asset_dir, report)
    _add_control_blocks(root, controllers, report, include_mimic_interfaces)

    masses = []
    for link in root.findall("link"):
        inertial = link.find("inertial")
        if inertial is None:
            continue
        mass = inertial.find("mass")
        masses.append({"link": link.get("name"), "mass_kg": float(mass.get("value"))})
    report["masses"] = masses
    report["total_mass_kg"] = round(sum(item["mass_kg"] for item in masses), 9)
    report["counts"] = {
        "links": len(root.findall("link")),
        "joints": len(root.findall("joint")),
        "movable": sum(1 for j in root.findall("joint") if j.get("type") != "fixed"),
    }
    report["actuated_joints"] = list(ACTUATED_JOINTS)
    report["mimic_joints"] = list(MIMIC_JOINTS) if include_mimic_interfaces else []

    ET.indent(root, space="  ")
    urdf_text = '<?xml version="1.0"?>\n' + ET.tostring(root, encoding="unicode")
    return PlantBuild(urdf_text=urdf_text, report=report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint-map", default=str(DEFAULT_JOINT_MAP))
    parser.add_argument("--asset-root", default=None)
    parser.add_argument("--controllers", default=None)
    parser.add_argument("--urdf-out", required=True)
    parser.add_argument("--report", default=None)
    parser.add_argument("--model-name", default="piper_x")
    args = parser.parse_args(argv)

    try:
        build = build_plant(
            joint_map_path=args.joint_map,
            asset_root=args.asset_root,
            controllers_yaml=args.controllers,
            model_name=args.model_name,
        )
    except PlantBuildError as exc:
        print(f"plant build failed: {exc}", file=sys.stderr)
        return 1

    urdf_out = Path(args.urdf_out)
    urdf_out.parent.mkdir(parents=True, exist_ok=True)
    urdf_out.write_text(build.urdf_text, encoding="utf-8")
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(build.report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    counts = build.report["counts"]
    print(
        f"plant built: {urdf_out} "
        f"({counts['links']} links, {counts['joints']} joints, "
        f"{counts['movable']} movable, {build.report['total_mass_kg']:.6f} kg, "
        f"{build.report['meshes']['references']} mesh references)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
