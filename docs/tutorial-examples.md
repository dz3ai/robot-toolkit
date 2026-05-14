# Tutorial Examples: Selected Challenges for robot-toolkit Demos

Based on `challenges.md` and current toolkit capabilities (Phase 15: IK, dynamics, trajectory, collision, path planning, ROS2), here are recommended tutorial examples.

---

## Priority 1: Immediate Tutorials (Current Capabilities)

### Tutorial 1: Dual-Arm Workspace Analysis
**Challenge**: "Limited usable shared workspace" (Challenges §1)

**Objective**: Visualize and analyze overlapping reachable workspace of two 6-DOF manipulators.

**Features demonstrated**:
- `six_dof_articulated()` model setup
- Forward kinematics for workspace sampling
- 3D visualization with matplotlib
- Workspace intersection calculation

**Code example**:
```python
from robot_ik import six_dof_articulated, RobotModel
import numpy as np
import matplotlib.pyplot as plt

# Setup dual arms with base offset
arm1 = six_dof_articulated()
arm2_base = np.array([1.5, 0, 0])  # 1.5m offset
arm2 = six_dof_articulated()
arm2.base_tf[:3, 3] = arm2_base

# Sample workspace points
workspace1 = sample_workspace(arm1, n_samples=5000)
workspace2 = sample_workspace(arm2, n_samples=5000)

# Find intersection
overlap = find_workspace_overlap(workspace1, workspace2)
print(f"Shared workspace volume: {overlap['volume']:.3f} m³")
```

**Learning outcomes**:
- Workspace sampling and visualization
- Dual-arm setup and coordinate transforms
- Overlap region analysis for task planning

---

### Tutorial 2: Self-Collision Detection
**Challenge**: "Self-collision risk" (Challenges §2)

**Objective**: Detect and visualize collisions between dual-arm links during coordinated motion.

**Features demonstrated**:
- `CollisionChecker` with primitive shapes
- Self-collision filtering for adjacent links
- Real-time collision checking during trajectory execution
- Visualization of collision points

**Code example**:
```python
from robot_ik.collision import CollisionChecker, Sphere, Capsule
from robot_ik import six_dof_articulated
import numpy as np

# Setup collision model for dual arms
checker = CollisionChecker()

# Add arm1 as capsules
for i in range(6):
    checker.add_shape(f"arm1_link{i}", Capsule(
        length=link_lengths[i], radius=0.05
    ))

# Add arm2 capsules (offset by 1.5m)
for i in range(6):
    checker.add_shape(f"arm2_link{i}", Capsule(
        length=link_lengths[i], radius=0.05,
        position=[1.5, 0, 0]
    ))

# Check collision during trajectory
for q1, q2 in dual_arm_trajectory:
    collision = checker.check_self_collision(
        arm1_pose=q1, arm2_pose=q2
    )
    if collision.collided:
        print(f"Collision at step {step}: {collision.contacts}")
        break
```

**Learning outcomes**:
- Collision primitive modeling
- Self-collision detection algorithms
- Trajectory safety validation

---

### Tutorial 3: Coordinated Trajectory Planning
**Challenge**: "Synchronized trajectory planning" (Challenges §3)

**Objective**: Generate time-synchronized trajectories for dual arms moving a shared object.

**Features demonstrated**:
- `waypoint_trajectory` for multi-waypoint paths
- Temporal alignment and velocity scaling
- Coordinated motion constraints

**Code example**:
```python
from robot_ik.trajectory import waypoint_trajectory, s_curve_profile

# Define shared object pick-and-place
pick_pose = np.array([0.5, 0.3, 0.4, 0, 0, 0])  # [x, y, z, rx, ry, rz]
place_pose = np.array([0.5, -0.3, 0.4, 0, 0, 0])

# Generate synchronized trajectory
waypoints = [pick_pose, place_pose]
duration = 3.0

# Arm1 trajectory (leading)
traj1 = waypoint_trajectory(
    waypoints, duration, profile_type="s-curve"
)

# Arm2 trajectory (synchronized, mirrored)
waypoints2 = [
    wp + np.array([0, 0.6, 0, 0, 0, 0])  # 0.6m gripper offset
    for wp in waypoints
]
traj2 = waypoint_trajectory(
    waypoints2, duration, profile_type="s-curve"
)

# Verify synchronization
for t1, t2 in zip(traj1.times, traj2.times):
    assert abs(t1 - t2) < 1e-6, "Trajectories not synchronized"
```

**Learning outcomes**:
- Multi-waypoint trajectory generation
- S-curve velocity profiling for smooth motion
- Dual-arm temporal coordination

---

### Tutorial 4: Collision-Free Path Planning (RRT*)
**Challenge**: "Complex real-time collision detection" + "Self-collision" (Challenges §2)

**Objective**: Plan collision-free paths for dual arms in shared workspace using RRT*.

**Features demonstrated**:
- `RRTStar` path planner
- Collision constraint integration
- Multi-robot path planning

**Code example**:
```python
from robot_ik.path_planning import RRTStar
from robot_ik.collision import CollisionChecker

# Setup RRT* with collision checking
planner = RRTStar(
    collision_checker=checker,
    max_iter=1000,
    goal_tolerance=0.01
)

# Plan paths for both arms
start1 = np.zeros(6)
goal1 = np.array([np.pi/2, 0, np.pi/4, 0, np.pi/2, 0])

start2 = np.zeros(6)
goal2 = np.array([np.pi/2, 0, -np.pi/4, 0, np.pi/2, 0])

# Plan sequentially (arm1 first, then arm2)
path1 = planner.plan(start1, goal1)
print(f"Arm1 path: {len(path1.waypoints)} waypoints")

# Re-plan arm2 considering arm1's final position
checker.set_obstacle("arm1_final", path1.waypoints[-1])
path2 = planner.plan(start2, goal2)
print(f"Arm2 path: {len(path2.waypoints)} waypoints")
```

**Learning outcomes**:
- Sampling-based path planning
- Collision constraint integration
- Sequential multi-robot planning

---

## Priority 2: Medium Tutorials (Require Extensions)

### Tutorial 5: Master-Slave Coordinated Grasping
**Challenge**: "Multiple control modes complexity" (Challenges §3)

**Objective**: Implement master-slave control where arm2 follows arm1 with offset.

**Required extensions**:
- Master-slave control framework (Phase 16)
- Real-time communication between two robot instances

**Code example**:
```python
from robot_ik import DynamicsSolver, six_dof_articulated

class MasterSlaveController:
    def __init__(self, master_arm, slave_arm, offset):
        self.master = master_arm
        self.slave = slave_arm
        self.offset = offset  # [x, y, z, rx, ry, rz]

    def update(self, master_q):
        # Compute slave target from master pose
        master_pose = fk(master_q)
        slave_pose = master_pose + self.offset

        # Solve IK for slave
        slave_q = ik_solve(slave_pose)
        return slave_q

# Usage
controller = MasterSlaveController(
    arm1, arm2, offset=np.array([0, 0.6, 0, 0, 0, 0])
)

for master_q in trajectory1:
    slave_q = controller.update(master_q)
    # Execute both arms simultaneously
```

**Learning outcomes**:
- Master-slave control architecture
- Real-time coordinated motion
- Offset transformation and IK solving

---

### Tutorial 6: Closed-Chain Constraint Control
**Challenge**: "Constraint motion control" (Challenges §3)

**Objective**: Control dual arms holding a shared object with closed-chain constraints.

**Required extensions**:
- Constraint-based programming (Phase 16)
- Hybrid position-force control

**Code example**:
```python
from robot_ik.constraints import ClosedChainConstraint

# Define closed-chain constraint
constraint = ClosedChainConstraint(
    arm1, arm2,
    object_length=0.6,  # Distance between grippers
    stiffness=1000,     # Position stiffness
    damping=50          # Damping
)

# Plan constrained motion
trajectory = plan_constrained_trajectory(
    start_pose, goal_pose,
    constraint=constraint,
    planner=RRTStar
)

# Execute with force feedback
for q1, q2 in trajectory:
    f1, f2 = measure_forces()
    q1_adj, q2_adj = constraint.update(q1, q2, f1, f2)
    execute(q1_adj, q2_adj)
```

**Learning outcomes**:
- Closed-chain kinematic constraints
- Force-position hybrid control
- Constrained trajectory optimization

---

## Priority 3: Advanced Tutorials (Future Phases)

### Tutorial 7: Dual-Arm Assembly with Force Control
**Challenge**: "Internal force control" + "Compliance control" (Challenges §4)

**Features**: Hybrid position-force control, peg-in-hole insertion

### Tutorial 8: Vision-Guided Dual-Arm Manipulation
**Challenge**: "Dual-view vision calibration" + "Occlusion problems" (Challenges §5)

**Features**: Multi-camera calibration, occlusion handling, visual servoing

### Tutorial 9: Real-Time Collision Avoidance with FCL
**Challenge**: "Complex real-time collision detection" (Challenges §2)

**Features**: Mesh-based collision, FCL integration, real-time performance

---

## Implementation Roadmap

### Phase 15b (Immediate - This Week)
- [ ] Tutorial 1: Workspace Analysis
- [ ] Tutorial 2: Self-Collision Detection
- [ ] Tutorial 3: Coordinated Trajectories
- [ ] Tutorial 4: RRT* Path Planning

### Phase 16 (Next Sprint)
- [ ] Master-slave control framework
- [ ] Tutorial 5: Master-Slave Grasping
- [ ] Constraint-based programming
- [ ] Tutorial 6: Closed-Chain Control

### Phase 17+ (Future)
- [ ] Force control integration
- [ ] Vision system integration
- [ ] FCL/mesh collision detection
- [ ] Tutorials 7-9

---

## Summary Table

| Tutorial | Challenge Section | Difficulty | Phase | Features Used |
|----------|------------------|------------|-------|---------------|
| 1. Workspace Analysis | §1 Kinematics | Beginner | 15b | FK, visualization |
| 2. Self-Collision | §2 Collision | Beginner | 15b | CollisionChecker |
| 3. Coordinated Trajectories | §3 Motion Planning | Intermediate | 15b | Trajectory module |
| 4. RRT* Path Planning | §2 Collision | Intermediate | 15b | RRTStar planner |
| 5. Master-Slave | §3 Control Modes | Advanced | 16 | New framework |
| 6. Closed-Chain | §3 Constraints | Advanced | 16 | Constraints |
| 7. Force Control | §4 Force/Interaction | Expert | 17+ | Hybrid control |
| 8. Vision Guidance | §5 Perception | Expert | 17+ | Vision system |
| 9. FCL Collision | §2 Real-Time | Expert | 17+ | Mesh collision |

---

## Next Steps

1. **Choose tutorial order**: Recommend implementing 1→2→3→4 first (all use current features)
2. **Create example scripts**: Add to `examples/tutorials/` directory
3. **Documentation**: Write Jupyter notebooks for each tutorial
4. **Testing**: Validate all examples run without external hardware
5. **Community feedback**: Publish as part of v0.3.0 documentation
