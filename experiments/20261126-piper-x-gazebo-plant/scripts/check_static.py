#!/usr/bin/env python3
"""Static acceptance checks for MVE-1 (no Gazebo server, no ROS graph).

This script independently re-parses the generated URDF and the SDF produced by
``gz sdf -p``. It does not trust the generator's own report: joint names,
types, limits, mimic relations and mesh resolution are checked against
``joint_map.yaml`` and the filesystem again.

Exit status is 0 only when every hard check passes; warnings are recorded but
do not change the exit status.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
PLANT_DIR = EXPERIMENT / "plant"
sys.path.insert(0, str(PLANT_DIR))

from piper_x_plant import (  # noqa: E402
    ACTUATED_JOINTS,
    MIMIC_JOINTS,
    PlantBuildError,
    build_plant,
    flatten_joint_map,
    load_joint_map,
    locate_asset_dir,
)

HARD = "hard"
WARN = "warn"


def _run(command: list[str], timeout: float = 60.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, capture_output=True, text=True, timeout=timeout, check=False
    )


def _parse_float(text: str | None) -> float | None:
    return None if text is None else float(text)


def _movable(joint: ET.Element) -> bool:
    return joint.get("type") not in ("fixed", "floating")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", default=None)
    parser.add_argument(
        "--joint-map",
        default=str(EXPERIMENT.parents[2] / "jcheng-simulation/docs/robots/piper_x/joint_map.yaml"),
    )
    parser.add_argument("--urdf-out", default=str(EXPERIMENT / "generated/piper_x_gazebo.urdf"))
    parser.add_argument("--sdf-out", default=str(EXPERIMENT / "generated/piper_x_gazebo.sdf"))
    parser.add_argument("--output", default=str(EXPERIMENT / "data/static_checks.json"))
    args = parser.parse_args(argv)

    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    def add(check_id: str, description: str, passed: bool, detail: Any, level: str = HARD):
        checks.append(
            {
                "id": check_id,
                "description": description,
                "status": "pass" if passed else "fail",
                "level": level,
                "detail": detail,
            }
        )

    def warn(check_id: str, description: str, detail: Any):
        checks.append(
            {
                "id": check_id,
                "description": description,
                "status": "warn",
                "level": WARN,
                "detail": detail,
            }
        )

    joint_map_path = Path(args.joint_map).resolve()
    joint_map = load_joint_map(joint_map_path)
    flat = flatten_joint_map(joint_map)

    try:
        build = build_plant(
            joint_map_path=joint_map_path,
            asset_root=args.asset_root,
            controllers_yaml=PLANT_DIR / "config/piper_x_controllers.yaml",
        )
    except (PlantBuildError, OSError) as exc:
        add("A1.0", "plant generator succeeds", False, str(exc))
        report = {
            "schema": "jcheng.piper_x_mve1_static.v1",
            "generated": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "summary": {"hard_failures": 1, "warnings": 0, "acceptance": {}},
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"static checks FAILED: {exc}", file=sys.stderr)
        return 1

    urdf_path = Path(args.urdf_out)
    urdf_path.parent.mkdir(parents=True, exist_ok=True)
    urdf_path.write_text(build.urdf_text, encoding="utf-8")

    # ---- A1: source and URDF -------------------------------------------------
    source = build.report["source"]
    add(
        "A1.1",
        "pinned source SHA-256 matches joint_map.yaml",
        all(item["match"] for item in source["files"].values()),
        source,
    )
    try:
        urdf_root = ET.parse(urdf_path).getroot()
        urdf_ok = True
        urdf_error = None
    except ET.ParseError as exc:  # pragma: no cover - generator writes valid XML
        urdf_root = None
        urdf_ok = False
        urdf_error = str(exc)
    urdf_joints = [] if urdf_root is None else urdf_root.findall("joint")
    add(
        "A1.2",
        "generated URDF is well-formed with 12 joints",
        urdf_ok and len(urdf_joints) == 12,
        {"well_formed": urdf_ok, "error": urdf_error, "joints": len(urdf_joints)},
    )

    # ---- A2: joints, limits, mimic against the checked-in contract -----------
    movable = {joint.get("name"): joint for joint in urdf_joints if _movable(joint)}
    expected_names = set(flat) - {"world_to_base_link", "flange_joint", "gripper_base_joint"}
    add(
        "A2.1",
        "movable joint set is exactly joint_map.yaml",
        set(movable) == expected_names,
        {
            "expected": sorted(expected_names),
            "actual": sorted(movable),
            "missing": sorted(expected_names - set(movable)),
            "unexpected": sorted(set(movable) - expected_names),
        },
    )

    limit_mismatches = []
    type_mismatches = []
    for name, joint in movable.items():
        entry = flat[name]
        if joint.get("type") != entry["type"]:
            type_mismatches.append(
                {"joint": name, "urdf": joint.get("type"), "joint_map": entry["type"]}
            )
        limit = joint.find("limit")
        if limit is None:
            limit_mismatches.append({"joint": name, "error": "no <limit>"})
            continue
        if entry["type"] == "revolute":
            expected = {
                "lower": entry["lower_rad"],
                "upper": entry["upper_rad"],
                "effort": entry["effort_nm"],
                "velocity": entry["velocity_rad_s"],
            }
        else:
            expected = {
                "lower": entry["lower_m"],
                "upper": entry["upper_m"],
                "effort": entry["effort_n"],
                "velocity": entry["velocity_m_s"],
            }
        actual = {key: _parse_float(limit.get(key)) for key in expected}
        for key, value in expected.items():
            if actual[key] is None or abs(actual[key] - float(value)) > 1e-9:
                limit_mismatches.append(
                    {"joint": name, "field": key, "urdf": actual[key], "joint_map": value}
                )
    add(
        "A2.2",
        "movable joint types match joint_map.yaml",
        not type_mismatches,
        type_mismatches or "all match",
    )
    add(
        "A2.3",
        "movable joint limits match joint_map.yaml (abs tol 1e-9)",
        not limit_mismatches,
        limit_mismatches or "all match",
    )

    mimic_mismatches = []
    for name, entry in flat.items():
        if not isinstance(entry.get("mimic"), dict):
            continue
        joint = movable.get(name)
        if joint is None:
            mimic_mismatches.append({"joint": name, "error": "missing from URDF"})
            continue
        mimic = joint.find("mimic")
        if mimic is None:
            mimic_mismatches.append({"joint": name, "error": "no <mimic>"})
            continue
        actual = {
            "joint": mimic.get("joint"),
            "multiplier": float(mimic.get("multiplier", "1")),
            "offset": float(mimic.get("offset", "0")),
        }
        expected = entry["mimic"]
        if (
            actual["joint"] != expected["joint"]
            or abs(actual["multiplier"] - float(expected["multiplier"])) > 1e-12
            or abs(actual["offset"] - float(expected["offset"])) > 1e-12
        ):
            mimic_mismatches.append(
                {"joint": name, "urdf": actual, "joint_map": expected}
            )
    add(
        "A2.4",
        "URDF mimic relations match joint_map.yaml (+0.5 / -0.5)",
        not mimic_mismatches and len(flat) > 0,
        mimic_mismatches or "gripper_joint1 +0.5, gripper_joint2 -0.5",
    )

    # ---- A3: mesh paths ------------------------------------------------------
    mesh_refs = []
    package_uris = []
    missing_meshes = []
    for link in urdf_root.findall("link"):
        for kind in ("visual", "collision"):
            for holder in link.findall(kind):
                mesh = holder.find("geometry/mesh")
                if mesh is None:
                    continue
                uri = mesh.get("filename", "")
                mesh_refs.append({"link": link.get("name"), "kind": kind, "uri": uri})
                if uri.startswith("package://"):
                    package_uris.append(uri)
                    continue
                path = Path(urlparse(uri).path)
                if not path.is_file():
                    missing_meshes.append(str(path))
    add(
        "A3.1",
        "every mesh URI resolves to an existing file",
        mesh_refs and not missing_meshes,
        {
            "references": len(mesh_refs),
            "unique": len({item["uri"] for item in mesh_refs}),
            "missing": missing_meshes,
        },
    )
    add(
        "A3.2",
        "no package:// URI remains in the plant URDF",
        not package_uris,
        package_uris or "none",
    )

    gz = shutil.which("gz")
    conversion = None
    sdf_root = None
    if gz is None:
        add("A3.3", "gz sdf -p conversion succeeds", False, "gz CLI not on PATH")
    else:
        try:
            conversion = _run([gz, "sdf", "-p", str(urdf_path)], timeout=60.0)
            sdf_ok = conversion.returncode == 0
            if sdf_ok:
                sdf_root = ET.fromstring(conversion.stdout)
        except (subprocess.TimeoutExpired, ET.ParseError) as exc:
            conversion = None
            sdf_ok = False
            conversion_error = str(exc)
        else:
            conversion_error = None
        bad_lines = []
        if conversion is not None:
            for line in conversion.stderr.splitlines():
                if any(
                    token in line
                    for token in (
                        "Error Code",
                        "is not modeled",
                        "parent joint",
                        "Unable to find",
                        "Not defined",
                        "not defined in SDF",
                    )
                ):
                    bad_lines.append(line)
        add(
            "A3.3",
            "gz sdf -p conversion succeeds with clean stderr",
            bool(sdf_ok and not bad_lines),
            {
                "exit": None if conversion is None else conversion.returncode,
                "stderr_lines": 0 if conversion is None else len(conversion.stderr.splitlines()),
                "stderr": "" if conversion is None else conversion.stderr,
                "bad_lines": bad_lines,
                "error": conversion_error,
            },
        )

    # ---- A4: SDF structure ---------------------------------------------------
    sdf_model = None if sdf_root is None else sdf_root.find("model")
    sdf_joints = [] if sdf_model is None else sdf_model.findall("joint")
    sdf_movable = {
        joint.get("name"): joint for joint in sdf_joints if _movable(joint)
    }
    add(
        "A4.1",
        "SDF keeps all 9 movable joints including the master gripper",
        set(sdf_movable) == expected_names and len(sdf_joints) >= 10,
        {
            "sdf_joints": sorted(joint.get("name") for joint in sdf_joints),
            "missing_movable": sorted(expected_names - set(sdf_movable)),
            "master_gripper_present": "gripper" in sdf_movable,
        },
    )

    sdf_mimic = []
    for name in MIMIC_JOINTS:
        joint = sdf_movable.get(name)
        axis = None if joint is None else joint.find("axis")
        mimic = None if axis is None else axis.find("mimic")
        sdf_mimic.append(
            {
                "joint": name,
                "mimic_present": mimic is not None,
                "parent": None if mimic is None else mimic.get("joint"),
                "multiplier": None if mimic is None else float(mimic.findtext("multiplier", "1")),
                "offset": None if mimic is None else float(mimic.findtext("offset", "0")),
                "reference": None if mimic is None else float(mimic.findtext("reference", "0")),
            }
        )
    mimic_ok = all(
        item["mimic_present"]
        and item["parent"] == "gripper"
        and abs(item["multiplier"] - (0.5 if item["joint"] == "gripper_joint1" else -0.5)) < 1e-12
        and abs(item["offset"]) < 1e-12
        for item in sdf_mimic
    )
    add(
        "A4.2",
        "SDF preserves mimic under <axis> with +0.5 / -0.5 and offset 0",
        mimic_ok,
        sdf_mimic,
    )

    sdf_mesh_uris = [] if sdf_root is None else [
        element.text or "" for element in sdf_root.iter("uri")
    ]
    sdf_missing = [
        uri for uri in sdf_mesh_uris
        if uri.startswith("file://") and not Path(urlparse(uri).path).is_file()
    ]
    add(
        "A4.3",
        "every SDF mesh URI resolves to an existing file",
        sdf_root is not None and sdf_mesh_uris and not sdf_missing,
        {
            "uris": len(sdf_mesh_uris),
            "missing": sdf_missing,
        },
    )

    # ---- host capability (informational) ------------------------------------
    physics_dir = Path("/opt/ros/jazzy/opt/gz_physics_vendor/lib")
    engines = []
    if physics_dir.is_dir():
        for path in sorted(physics_dir.glob("*plugin.so")):
            payload = path.read_bytes()
            engines.append(
                {
                    "library": path.name,
                    "declares_set_mimic_feature": b"SetMimicConstraintFeature" in payload,
                    "contains_unsupported_message": b"does not support mimic" in payload,
                }
            )
    gz_version = None
    if gz is not None:
        try:
            version = _run([gz, "sim", "--versions"], timeout=20.0)
            gz_version = version.stdout.strip() or version.stderr.strip()
        except subprocess.TimeoutExpired:
            gz_version = "timeout"
    environment = {
        "gz_sim_versions": gz_version,
        "physics_engines": engines,
    }
    warn(
        "ENV.1",
        "installed physics engines and their SDF mimic capability",
        environment,
    )

    # ---- findings from the source data --------------------------------------
    asset_dir = locate_asset_dir(args.asset_root)
    xacro_root = ET.parse(
        asset_dir / "piper_x/urdf/piper_x_with_gripper_description.xacro"
    ).getroot()
    for link in xacro_root.findall("link"):
        if link.find("inertial") is None:
            findings.append(
                {
                    "id": "massless_source_link",
                    "link": link.get("name"),
                    "detail": (
                        "the MIT xacro declares this link without <inertial>; "
                        "urdf2sdf drops it (and its parent joint) unless the "
                        "plant supplies a placeholder mass"
                    ),
                }
            )
    axis_mismatches = [
        {
            "joint": record["name"],
            "urdf_axis": record.get("axis"),
            "joint_map_axis": record.get("map_axis"),
        }
        for record in build.report["joints"]
        if record.get("map_axis") is not None and record.get("axis_matches_map") is False
    ]
    if axis_mismatches:
        findings.append(
            {
                "id": "joint_map_axis_mismatch",
                "detail": (
                    "joint_map.yaml records a different <axis> for these gripper "
                    "joints than the pinned xacro; the plant keeps the URDF axis "
                    "(geometry authority) and records the discrepancy"
                ),
                "items": axis_mismatches,
            }
        )
    warnings_count = sum(1 for check in checks if check["status"] == "warn")
    hard_failures = sum(1 for check in checks if check["status"] == "fail")

    acceptance = {}
    for check in checks:
        if check["id"].startswith(("A1", "A2", "A3", "A4")):
            prefix = check["id"].split(".")[0]
            acceptance[prefix] = (
                "fail" if check["status"] == "fail"
                else "pass" if acceptance.get(prefix) != "fail"
                else "fail"
            )
    acceptance["A5"] = "runtime-only"
    acceptance["A6"] = "runtime-only"
    acceptance["A7"] = "runtime-only"

    report = {
        "schema": "jcheng.piper_x_mve1_static.v1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "joint_map": str(joint_map_path),
        "urdf": str(urdf_path),
        "plant_report": build.report,
        "environment": environment,
        "checks": checks,
        "findings": findings,
        "summary": {
            "hard_failures": hard_failures,
            "warnings": warnings_count,
            "acceptance": acceptance,
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if conversion is not None:
        Path(args.sdf_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.sdf_out).write_text(conversion.stdout, encoding="utf-8")

    for check in checks:
        mark = {"pass": "PASS", "fail": "FAIL", "warn": "WARN"}[check["status"]]
        print(f"[{mark}] {check['id']} {check['description']}")
    print(
        f"static checks: {hard_failures} hard failure(s), {warnings_count} warning(s); "
        f"report -> {output}"
    )
    return 0 if hard_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
