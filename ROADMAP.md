# robot-toolkit Roadmap

Version: 0.2.0 | Last updated: 2026-05-10

## Project Summary

6-DOF serial manipulator toolkit: inverse kinematics, rigid body dynamics,
URDF import, and C++ acceleration. Pure Python fallbacks for everything.

---

## Completed

### Phase 1 — Inverse Kinematics (2026-05-08)
- [x] DH parameter forward kinematics
- [x] Damped least-squares IK (Levenberg-Marquardt)
- [x] Analytical Jacobian computation
- [x] Joint limit enforcement (gradient projection)
- [x] Pre-built models: 6-DOF articulated, spherical wrist
- [x] 3D matplotlib visualization (arm + target frame)
- [x] Test suite: FK identity, IK roundtrip, Jacobian, joint limits, benchmark
- [x] Performance: ~3 ms avg, <0.1 mm position accuracy

### Phase 2 — C++ IK Extension (2026-05-09)
- [x] pybind11 C++ extension for FK + Jacobian + IK loop
- [x] 137x speedup over pure Python (~0.09 ms avg)
- [x] Graceful fallback when C++ not built

### Phase 3 — Rigid Body Dynamics (2026-05-09)
- [x] Recursive Newton-Euler inverse dynamics (RNEA)
- [x] Composite Rigid Body Algorithm (CRBA) forward dynamics
- [x] Gravity torque, Coriolis, inertia matrix computation
- [x] Inverse/forward dynamics roundtrip tests (50 configs)
- [x] Pendulum gravity validation against analytical solution

### Phase 4 — C++ Dynamics Extension (2026-05-09)
- [x] pybind11 C++ RNEA implementation
- [x] 358x speedup over pure Python dynamics
- [x] 50-configuration verification against Python reference

### Phase 5 — URDF + Packaging (2026-05-09)
- [x] URDF parser: mass, COM, inertia extraction
- [x] URDF to DH parameter conversion
- [x] `robot_ik` namespace package structure
- [x] `setup.py` for pip install + C++ build_ext

---

## Planned

### Phase 6 — Trajectory Planning
- [ ] Joint-space interpolation (linear, cubic, quintic)
- [ ] Cartesian-space straight-line interpolation
- [ ] Time-optimal trajectory with velocity/acceleration limits
- [ ] Trapezoidal and S-curve velocity profiles
- [ ] Waypoint sequencing with smooth blends

### Phase 7 — Collision Checking
- [ ] Link geometry: capsule / sphere approximation per link
- [ ] Self-collision detection (link-link distance)
- [ ] Environment collision: obstacle spheres/boxes
- [ ] Collision-free IK (reject colliding solutions)

### Phase 8 — Motion Control Interface
- [ ] Joint position PID controller
- [ ] Computed-torque (inverse dynamics + PD) controller
- [ ] Cartesian impedance controller
- [ ] Simulation timestep loop with dynamics integration

### Phase 9 — Advanced IK
- [ ] Redundant robot support (7+ DOF)
- [ ] Null-space optimization (joint limit avoidance, manipulability)
- [ ] IK with obstacle avoidance constraints
- [ ] Multiple solution enumeration
- [ ] Configuration-space singularity mapping

### Phase 10 — Visualization & Tooling Upgrade
- [ ] Real-time 3D viewer (switch from matplotlib to rerun.io or meshcat)
- [ ] URDF mesh rendering (STL/DAE loading)
- [ ] Workspace envelope visualization (reachable set)
- [ ] Manipulability ellipsoid display
- [ ] Animation playback of trajectories

### Phase 11 — Real Robot Integration
- [ ] Joint state publisher/subscriber (ROS 2 bridge)
- [ ] Real-time control loop (<1 kHz) with C++ backend
- [ ] Hardware abstraction: joint command/feedback interface
- [ ] Safety: joint limit enforcement, collision stop, E-stop

### Phase 12 — Quality & Distribution
- [ ] CI pipeline (GitHub Actions): test, build C++ wheels, lint
- [ ] PyPI package: binary wheels for Linux/macOS/Windows
- [ ] API documentation (Sphinx or mkdocs)
- [ ] Example gallery: pick-and-place, drawing, teleoperation
- [ ] Type annotations pass (mypy strict)

---

## Current Stats

| Metric | Value |
|--------|-------|
| Python LOC | ~1,083 |
| C++ LOC | ~665 |
| Total files | 14 (source) |
| Test cases | ~15 |
| Version | 0.2.0 |
| License | MIT |

---

## Priority Order

Short-term (next session):
1. Trajectory planning (Phase 6)
2. CI pipeline (Phase 12 partial)

Medium-term:
3. Collision checking (Phase 7)
4. Motion control (Phase 8)
5. Advanced IK (Phase 9)

Long-term:
6. Visualization upgrade (Phase 10)
7. Real robot integration (Phase 11)
8. Full distribution (Phase 12)
