"""Solve IK for a 6-DOF articulated robot at target position [0.5, 0.3, 0.4]."""

import numpy as np
from robot_ik import six_dof_articulated

# Create default 6-DOF articulated robot
robot = six_dof_articulated()

# Build a 4x4 homogeneous transform for target position [0.5, 0.3, 0.4]
# Orientation: identity rotation (end-effector pointing along approach axis)
target = np.eye(4)
target[:3, 3] = [0.5, 0.3, 0.4]

print(f"Target position: {target[:3, 3]}")
print(f"Target rotation:\n{target[:3, :3]}")

# Solve IK with damped least-squares
success, q, iters, errors = robot.ik_solve(target)

if success:
    print(f"\nIK converged in {iters} iterations")
    print(f"Joint angles (deg): {np.degrees(q)}")
    print(f"Joint angles (rad): {q}")

    # Verify solution with forward kinematics
    T_fk = robot.forward_kinematics(q)
    pos_error = np.linalg.norm(T_fk[:3, 3] - target[:3, 3])
    print(f"\nFK verification:")
    print(f"  Achieved position: {T_fk[:3, 3]}")
    print(f"  Position error:    {pos_error:.6f} m")
else:
    print(f"\nIK failed after {iters} iterations")
    print(f"Final position error: {errors[-1]:.6f} m")
    print("Target may be unreachable or near a singularity.")
