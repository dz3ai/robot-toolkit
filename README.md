# 6-DOF Inverse Kinematics Solver

Jacobian-based iterative inverse kinematics for arbitrary 6-DOF serial manipulators.
Given a desired end-effector pose, computes joint angles using damped least-squares.

**Key features:**
- DH parameter forward kinematics
- Damped least-squares IK (Levenberg-Marquardt)
- Analytical Jacobian computation
- Joint limit enforcement
- Pre-built models: 6-DOF articulated, spherical wrist
- 3D visualization
- <5 ms per solve (typical)

## Quick Start

```bash
pip install -r requirements.txt
python test_ik.py
python visualize.py
```

## Usage

```python
from ik_solver import six_dof_articulated
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
from ik_solver import RobotModel, DHParam

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
ik_solver.py     — Core: DH FK, Jacobian, DLS IK solver, robot models
visualize.py     — 3D arm visualization, convergence plots
test_ik.py       — 7 tests + benchmark suite
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
