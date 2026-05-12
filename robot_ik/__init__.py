"""robot-ik — Fast 6-DOF Inverse Kinematics and Rigid Body Dynamics

C++ accelerated robotics toolkit with Python API.
"""

from robot_ik.ik_solver import (
    DHParam, RobotModel, dh_transform,
    six_dof_articulated, spherical_wrist_6dof,
)

from robot_ik.robot_dyn import (
    LinkInertia, RobotDynamicsModel, DynamicsSolver,
    six_dof_articulated_dyn,
)

from robot_ik.urdf_parser import (
    urdf_to_dynamics_model, quick_urdf,
)

from robot_ik.trajectory import (
    TrajectoryResult,
    joint_linear_interpolation,
    joint_cubic_interpolation,
    joint_quintic_interpolation,
    cartesian_straight_line,
    trapezoidal_velocity_profile,
    s_curve_profile,
    waypoint_trajectory,
)

# Try to import C++ extensions (optional)
try:
    from robot_ik.ik_fast import forward_kinematics as _fk_cpp
    from robot_ik.ik_fast import compute_jacobian as _jac_cpp
    from robot_ik.ik_fast import ik_solve as _ik_cpp
    HAS_IK_FAST = True
except ImportError:
    HAS_IK_FAST = False

try:
    from robot_ik.robot_dyn_fast import inverse_dynamics as _id_cpp
    HAS_DYN_FAST = True
except ImportError:
    HAS_DYN_FAST = False


__version__ = "0.2.0"
__all__ = [
    "DHParam", "RobotModel", "dh_transform",
    "six_dof_articulated", "spherical_wrist_6dof",
    "LinkInertia", "RobotDynamicsModel", "DynamicsSolver",
    "six_dof_articulated_dyn",
    "urdf_to_dynamics_model", "quick_urdf",
    "TrajectoryResult",
    "joint_linear_interpolation",
    "joint_cubic_interpolation",
    "joint_quintic_interpolation",
    "cartesian_straight_line",
    "trapezoidal_velocity_profile",
    "s_curve_profile",
    "waypoint_trajectory",
    "HAS_IK_FAST", "HAS_DYN_FAST",
]
