"""
Solve IK for target position [0.5, 0.3, 0.4].

Uses damped least-squares solver from robot-toolkit.
Verifies the solution with forward kinematics.
"""

import numpy as np
from robot_ik import six_dof_articulated


def main():
    # Create default 6-DOF articulated robot
    robot = six_dof_articulated()

    # Target position
    target_pos = np.array([0.5, 0.3, 0.4])

    # Build 4x4 homogeneous transform (identity orientation)
    target = np.eye(4)
    target[:3, 3] = target_pos

    # Solve IK
    success, q, iters, errors = robot.ik_solve(
        target,
        max_iterations=300,
        position_tolerance=1e-4,
    )

    if success:
        print(f"IK solved in {iters} iterations")
        print(f"Joint angles (deg): {np.degrees(q)}")
        print(f"Joint angles (rad): {q}")

        # Verify with FK
        T = robot.forward_kinematics(q)
        fk_pos = T[:3, 3]
        pos_err = np.linalg.norm(fk_pos - target_pos)
        print(f"FK position:       {fk_pos}")
        print(f"Target position:   {target_pos}")
        print(f"Position error:    {pos_err:.6f} m")

        if pos_err < 1e-3:
            print("PASS: Solution verified.")
        else:
            print("WARN: Position error exceeds 1mm threshold.")
    else:
        print(f"IK FAILED after {iters} iterations")
        print(f"Final error: {errors[-1]:.6f}")
        print("Target may be outside the robot's reachable workspace.")


if __name__ == "__main__":
    main()
