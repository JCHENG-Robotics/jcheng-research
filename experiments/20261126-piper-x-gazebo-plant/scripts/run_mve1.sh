#!/usr/bin/env bash
# MVE-1 orchestration: static checks -> Gazebo plant -> controllers -> probe.
#
# Every wait is a state poll (1 s interval, bounded deadline); there is no fixed
# long sleep. The plant is confined to ROS_DOMAIN_ID=43 and lives under
# /sim/piper_x so it can coexist with other domain-43 plants that also use the
# bare /sim namespace (the repo's mock plant and the migrated gate2 arm).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP="$(cd "${HERE}/.." && pwd)"
cd "${EXP}"
mkdir -p logs data generated

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
set -u

export ROS_DOMAIN_ID=43
export GZ_PARTITION=jcheng-sim
export PYTHONUNBUFFERED=1

MANAGER="/sim/piper_x/controller_manager"
PLANT_PREFIX="/sim/piper_x"
LPID=""

fail() {
  echo "MVE-1 FAILURE: $*" >&2
}

stop_plant() {
  [[ -n "${LPID}" ]] || return 0
  kill -INT "${LPID}" 2>/dev/null || true
  for _ in $(seq 1 20); do
    kill -0 "${LPID}" 2>/dev/null || break
    sleep 1
  done
  kill -TERM "${LPID}" 2>/dev/null || true
  for _ in $(seq 1 5); do
    kill -0 "${LPID}" 2>/dev/null || break
    sleep 1
  done
  kill -KILL "${LPID}" 2>/dev/null || true
  # The Gazebo process can outlive the launch wrapper; the world path is unique.
  for pid in $(pgrep -f '[p]iper_x_lab.sdf'); do kill -INT "${pid}" 2>/dev/null || true; done
  for _ in $(seq 1 10); do
    pgrep -f '[p]iper_x_lab.sdf' >/dev/null 2>&1 || break
    sleep 1
  done
  for pid in $(pgrep -f '[p]iper_x_lab.sdf'); do kill -TERM "${pid}" 2>/dev/null || true; done
  sleep 1
  for pid in $(pgrep -f '[p]iper_x_lab.sdf'); do kill -KILL "${pid}" 2>/dev/null || true; done
}
trap stop_plant EXIT

for tool in ros2 gz python3; do
  command -v "${tool}" >/dev/null 2>&1 || { fail "${tool} not on PATH"; exit 1; }
done
python3 -c 'import rclpy, control_msgs, trajectory_msgs' >/dev/null 2>&1 || {
  fail "rclpy/control_msgs/trajectory_msgs not importable"
  exit 1
}

echo "== 0. preflight (no stale Piper X plant, no /sim/piper_x graph) =="
if pgrep -f '[p]iper_x_lab.sdf' >/dev/null 2>&1; then
  fail "a stale Piper X Gazebo server is already running"
  exit 1
fi
if timeout 10 ros2 topic list 2>/dev/null | grep -q "^${PLANT_PREFIX}"; then
  fail "another process already publishes ${PLANT_PREFIX}/* on domain 43"
  exit 1
fi
timeout 15 ros2 node list > logs/domain43_nodes_before.txt 2>/dev/null || true
timeout 15 ros2 topic list > logs/domain43_topics_before.txt 2>/dev/null || true
{
  echo "domain-43 nodes before launch:"
  cat logs/domain43_nodes_before.txt
  echo "other /sim publishers (not this plant):"
  grep -E '^/sim(/[^p]|$)' logs/domain43_topics_before.txt || true
} | tee logs/shared_domain_before.txt

echo "== 1. static checks (A1-A4) =="
if ! python3 scripts/check_static.py 2>&1 | tee logs/static_checks.log; then
  fail "static acceptance checks"
  exit 1
fi

urdf_sha="$(sha256sum generated/piper_x_gazebo.urdf | awk '{print $1}')"
echo "generated URDF sha256: ${urdf_sha}" | tee logs/urdf_sha256.txt

echo "== 2. launch Gazebo plant (domain 43, ${PLANT_PREFIX}) =="
ros2 launch plant/launch/piper_x_gazebo.launch.py headless:=true \
  > logs/mve1_launch.log 2>&1 &
LPID=$!
echo "${LPID}" > logs/launch.pid
echo "launch pid=${LPID}, log=logs/mve1_launch.log"

ready=0
start_epoch=$(date +%s)
for _ in $(seq 1 90); do
  if ! kill -0 "${LPID}" 2>/dev/null; then
    echo "launch process exited before controllers became active"
    break
  fi
  if timeout 10 ros2 control list_controllers -c "${MANAGER}" \
      > logs/controllers_startup.txt 2>/dev/null; then
    if grep -Eq 'joint_state_broadcaster.*active' logs/controllers_startup.txt \
        && grep -Eq 'arm_controller.*active' logs/controllers_startup.txt \
        && grep -Eq 'gripper_controller.*active' logs/controllers_startup.txt; then
      ready=1
      break
    fi
  fi
  sleep 1
done
if [[ "${ready}" -ne 1 ]]; then
  fail "controllers did not become active within 90 s"
  tail -n 80 logs/mve1_launch.log >&2
  exit 1
fi
startup_s=$(( $(date +%s) - start_epoch ))
echo "all controllers active after ${startup_s} s"
cat logs/controllers_startup.txt

echo "== 3. ROS graph and domain isolation (A5/A7) =="
timeout 15 ros2 node list > logs/ros_nodes.txt 2>/dev/null || true
timeout 15 ros2 topic list > logs/ros_topics.txt 2>/dev/null || true
timeout 15 ros2 topic list > logs/domain43_topics.txt 2>/dev/null || true

domain_ok=1
: > logs/domain_isolation.txt
for domain in 0 41 42; do
  out="$(ROS_DOMAIN_ID="${domain}" timeout 15 ros2 topic list 2>/dev/null || true)"
  matches="$(printf '%s\n' "${out}" | grep -E "^${PLANT_PREFIX}(/|$)" || true)"
  {
    echo "domain ${domain}: $(printf '%s\n' "${out}" | grep -c . || true) topics; ${PLANT_PREFIX} matches: ${matches:-none}"
  } >> logs/domain_isolation.txt
  if [[ -n "${matches}" ]]; then
    domain_ok=0
  fi
done
if grep -qx "${PLANT_PREFIX}/joint_states" logs/domain43_topics.txt; then
  joint_states_visible=1
else
  joint_states_visible=0
  domain_ok=0
fi
{
  echo "domain 43: ${PLANT_PREFIX}/joint_states visible=${joint_states_visible}"
  echo "domain isolation result: $([[ "${domain_ok}" -eq 1 ]] && echo pass || echo fail)"
} >> logs/domain_isolation.txt
cat logs/domain_isolation.txt

echo "== 4. trajectory probe (A5/A6) =="
python3 scripts/trajectory_probe.py --output data/runtime_probe.json \
  > logs/trajectory_probe.log 2>&1
probe_rc=$?
cat logs/trajectory_probe.log
if [[ "${probe_rc}" -ne 0 ]]; then
  fail "trajectory probe returned ${probe_rc}"
fi

echo "== 5. post-run state =="
timeout 15 ros2 control list_controllers -c "${MANAGER}" \
  > logs/controllers_after.txt 2>/dev/null || true
cat logs/controllers_after.txt

timeout 15 gz topic -e -t /world/piper_x_lab/pose/info -n 1 \
  > logs/pose_info.txt 2>&1 || true
python3 - <<'PY' > data/base_pose.json
import json
import re
from pathlib import Path
text = Path("logs/pose_info.txt").read_text(encoding="utf-8", errors="replace")
result = {"found": False}
match = re.search(r'name:\s*"base_link".*?position\s*\{([^}]*)\}', text, re.S)
if match:
    values = {"x": 0.0, "y": 0.0, "z": 0.0}
    for key, value in re.findall(r'([xyz]):\s*([-+0-9.eE]+)', match.group(1)):
        values[key] = float(value)
    result = {"found": True, "position": values}
print(json.dumps(result, indent=2))
PY
cat data/base_pose.json

python3 - <<'PY'
import json
import re
from pathlib import Path

log = Path("logs/mve1_launch.log").read_text(encoding="utf-8", errors="replace")
patterns = {
    "mimic": r".*mimic.*",
    "mesh_error": r".*(?:Unable to find|not found|failed to load).*(?:mesh|Mesh|uri|URI).*",
    "physics": r".*(?:Physics|physics).*(?:engine|Engine).*",
    "command_limits": r".*(?:command limits|limits are ignored|ignoring).*",
    "errors": r".*(?:\[Err\]|Error Code).*",
}
findings = {"log_lines": len(log.splitlines()), "patterns": {}}
for name, pattern in patterns.items():
    matches = [match.group(0).strip() for match in re.finditer(pattern, log, re.I)]
    findings["patterns"][name] = {
        "count": len(matches),
        "examples": matches[:10],
    }
Path("data/log_findings.json").write_text(
    json.dumps(findings, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(findings["patterns"], indent=2))
PY

echo "== 6. shutdown =="
stop_plant
LPID=""
echo "gz survivors after shutdown: $(pgrep -c -f '[p]iper_x_lab.sdf' 2>/dev/null || echo 0)" \
  | tee logs/shutdown.txt

echo "== 7. summary =="
python3 - <<'PY'
import json
from pathlib import Path

probe = json.loads(Path("data/runtime_probe.json").read_text())
static = json.loads(Path("data/static_checks.json").read_text())
isolation = Path("logs/domain_isolation.txt").read_text()
print("static acceptance:", static["summary"]["acceptance"])
print("runtime pass:", probe.get("pass"))
print("arm max abs error (rad):", probe.get("arm_max_abs_error_rad"))
print("gripper error (m):", probe.get("gripper_error_m"))
print("mimic:", probe.get("mimic"))
print("domain isolation:", "pass" if "result: pass" in isolation else "fail")
if probe.get("errors"):
    print("probe errors:", probe["errors"])
PY

if [[ "${probe_rc}" -ne 0 || "${domain_ok}" -ne 1 ]]; then
  exit 1
fi
exit 0
