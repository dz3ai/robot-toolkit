# robot-toolkit

[![CI](https://github.com/dz3ai/robot-toolkit/workflows/CI/badge.svg)](https://github.com/dz3ai/robot-toolkit/actions)
[![codecov](https://codecov.io/gh/dz3ai/robot-toolkit/branch/main/graph/badge.svg)](https://codecov.io/gh/dz3ai/robot-toolkit)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Fast 6-DOF serial manipulator toolkit with IK, rigid body dynamics, and trajectory planning.

**Key features:**
- DH parameter forward kinematics
- Damped least-squares IK (Levenberg-Marquardt)
- Geometric Jacobian computation
- Rigid body dynamics (RNEA, CRBA)
- Trajectory planning (linear, cubic, quintic, trapezoidal, S-curve, Cartesian, waypoints)
- C++ extensions (137x faster IK, 358x faster dynamics)
- URDF parser
- 3D visualization

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Run tests
pytest test_ik.py test_dyn.py test_trajectory.py

# Run specific test suites
python test_ik.py
python test_dyn.py
python test_trajectory.py
```

## Usage

```python
from robot_ik import six_dof_articulated
import numpy as np

robot = six_dof_articulated()

# Define target pose as 4x4 homogeneous transform
target = np.array([
    [0, -1,  0, 0.5],
    [0,  0, -1, 0.2],
    [1,  0,  0, 0.4],
    [0,  0,  0, 1.0],
])

# Solve IK
success, joint_angles, iterations, errors = robot.ik_solve(target)
print(f"Solved in {iterations} iterations, angles: {joint_angles}")

# Verify
T = robot.forward_kinematics(joint_angles)
print(f"Position error: {np.linalg.norm(T[:3,3] - target[:3,3]):.6f} m")
```

## Custom Robot

```python
from robot_ik import RobotModel, DHParam
import numpy as np

my_robot = RobotModel([
    DHParam(a=0,   alpha=-np.pi/2, d=0.35, theta=0),
    DHParam(a=0.6, alpha=0,        d=0,    theta=0),
    DHParam(a=0.1, alpha=-np.pi/2, d=0,    theta=0),
    DHParam(a=0,   alpha=np.pi/2,  d=0.4,  theta=0),
    DHParam(a=0,   alpha=-np.pi/2, d=0,    theta=0),
    DHParam(a=0,   alpha=0,        d=0.08, theta=0),
], joint_limits=[(-3.14, 3.14)] * 6)
```

## Performance

| Metric | Value |
|--------|-------|
| Avg solve time | ~3 ms |
| P50 solve time | ~2 ms |
| P95 solve time | ~8 ms |
| Typical iterations | 5-15 |
| Position accuracy | <0.1 mm |
| Orientation accuracy | <0.001 rad |

Benchmarked on 6-DOF articulated robot, 200 random target poses.

## Architecture

```
robot_ik/
├── ik_solver.py        — Core: DH FK, Jacobian, DLS IK solver, robot models
├── robot_dyn.py        — Rigid body dynamics: RNEA, CRBA, mass matrix
├── trajectory.py       — Trajectory planning: interpolation, velocity profiles, waypoints
├── urdf_parser.py      — URDF to dynamics model converter
├── visualize.py        — 3D arm visualization, convergence plots
└── __init__.py         — Package exports

test_ik.py              — 7 IK tests + benchmark suite
test_dyn.py             — Dynamics tests
test_trajectory.py      — 12 trajectory planning tests
```




## C++ Extension (137x faster)

```bash
python setup.py build_ext --inplace
```

```python
from ik_fast_wrapper import FastIKSolver

solver = FastIKSolver(dh_params, joint_limits)
success, angles, iters, errors = solver.ik_solve(target_pose)
# Average: 0.09 ms (vs 12.6 ms pure Python)
```

| Metric | Python | C++ | Speedup |
|--------|--------|-----|---------|
| Avg solve | 12.6 ms | 0.09 ms | **137x** |
| P50 solve | 5.4 ms | 0.03 ms | 180x |
| P95 solve | 36.9 ms | 0.56 ms | 66x |

## License

MIT — see LICENSE file.
