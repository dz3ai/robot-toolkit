# robot-toolkit ROS2 Package

ROS 2 integration for robot-toolkit manipulator library.

## Package Structure

```
ros2/
├── package.xml           # ROS2 package manifest
├── setup.py             # Python package setup
├── resource/
│   └── robot_toolkit    # Marker file
├── robot_toolkit_ros/
│   ├── __init__.py
│   └── ik_node.py       # IK service server node
├── launch/
│   └── ik_server.launch.py
└── test/
    └── test_copyright.py
    └── test_flake8.py
```

## Installation

```bash
# Copy to ROS2 workspace
cp -r ros2 ~/ros2_ws/src/robot_toolkit_ros

# Install dependencies
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build --packages-select robot_toolkit_ros

# Source
source install/setup.bash
```

## Usage

### IK Server Node

```bash
ros2 run robot_toolkit_ros ik_node
```

### Python API

```python
from robot_toolkit_ros import IKServiceClient

client = IKServiceClient()
result = client.solve_ik(target_pose)
print(f"Solution: {result.joint_angles}")
```

## Topics/Services

### Services

- `/solve_ik` (robot_toolkit_msgs/srv/SolveIK): Solve inverse kinematics
  - Request: target_pose (geometry_msgs/Pose)
  - Response: joint_angles (sensor_msgs/JointState), success (bool)

### Parameters

- `/robot_toolkit/damping_lambda`: DLS damping factor (default: 0.01)
- `/robot_toolkit/max_iterations`: IK max iterations (default: 100)

## Nodes

### ik_node

Inverse kinematics server node.

**Subscribers:**
- None

**Publishers:**
- `/joint_states` (sensor_msgs/JointState): Current joint configuration

**Services:**
- `/solve_ik`: Solve IK for target pose

**Parameters:**
- `damping_lambda`: DLS damping factor
- `max_iterations`: Maximum IK iterations

## Launch Files

### ik_server.launch.py

Launch the IK server node.

```bash
ros2 launch robot_toolkit_ros ik_server.launch.py
```

## Dependencies

- ROS 2 Humble/Foxy
- Python 3.8+
- robot-toolkit (pip install robot-toolkit)
- geometry_msgs
- sensor_msgs
- std_msgs

## Contributing

When adding new ROS2 nodes:
1. Create node in `robot_toolkit_ros/`
2. Add launch file in `launch/`
3. Update this README
4. Add tests in `test/`
