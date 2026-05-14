#!/usr/bin/env python3
"""
Debug script to investigate the 3x numerical discrepancy in test_pendulum_gravity.

Problem:
- Single pendulum at 30 degrees
- Expected gravity torque: mgL sin(θ) = 1.0 * 9.81 * 0.5 * sin(30°) = 2.45 Nm
- Actual computed torque: ~7.36 Nm (3x error!)

This script traces through the RNEA algorithm step by step.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from robot_ik import RobotDynamicsModel, LinkInertia, DynamicsSolver


def test_pendulum_debug():
    """Debug pendulum gravity computation."""
    print("=" * 70)
    print("Debugging test_pendulum_gravity")
    print("=" * 70)

    # Setup model (same as test)
    model = RobotDynamicsModel(
        dh_a=np.array([1.0]),
        dh_alpha=np.array([0.0]),
        dh_d=np.array([0.0]),
        links=[
            LinkInertia(
                mass=1.0,
                com=np.array([0.5, 0.0, 0.0]),
                inertia=np.array([[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]]),
            )
        ],
        gravity=np.array([-9.81, 0.0, 0.0]),
        joint_damping=np.zeros(1),
    )

    solver = DynamicsSolver(model)

    # Test at 30 degrees
    theta_deg = 30
    theta = np.deg2rad(theta_deg)
    print(f"\nConfiguration: {theta_deg}° = {theta:.4f} rad")
    print(f"Gravity vector: {model.gravity}")
    print(f"Link mass: {model.links[0].mass} kg")
    print(f"Link COM: {model.links[0].com} m (in link frame)")
    print(f"Link length (a): {model.dh_a[0]} m")

    # Compute expected value
    expected = model.links[0].mass * 9.81 * model.links[0].com[0] * np.sin(theta)
    print(f"\nExpected torque (analytical): mgL sin(θ)")
    print(f"  = {model.links[0].mass} * 9.81 * {model.links[0].com[0]} * sin({theta:.4f})")
    print(f"  = {expected:.6f} Nm")

    # Compute actual value
    tau = solver.gravity_torque(np.array([theta]))
    print(f"\nActual torque (RNEA): {tau[0]:.6f} Nm")
    print(f"Error: {abs(tau[0] - expected):.6f} Nm")
    print(f"Error ratio: {abs(tau[0] / expected):.2f}x")

    # Manual RNEA step-by-step
    print("\n" + "=" * 70)
    print("Manual RNEA Computation (Step-by-Step)")
    print("=" * 70)

    # Forward kinematics
    print("\n[Forward Pass - Kinematics]")
    T0 = np.eye(4)
    print(f"T0 (base):\n{T0}")

    # DH transformation for link 1
    c, s = np.cos(theta), np.sin(theta)
    T1 = np.array(
        [
            [c, -s, 0, model.dh_a[0] * c],
            [s, c, 0, model.dh_a[0] * s],
            [0, 0, 1, model.dh_d[0]],
            [0, 0, 0, 1],
        ]
    )
    print(f"\nT1 (link 1 at θ={theta:.4f}):\n{T1}")

    # COM position in base frame
    com_base = T1[:3, :3] @ model.links[0].com + T1[:3, 3]
    print(f"\nCOM position (base frame): {com_base}")

    # Forward pass - velocities
    print("\n[Forward Pass - Velocities]")
    g = model.gravity
    print(f"Gravity: {g}")
    print(f"a_origin[0] = -g = {-g}")

    z = np.array([0.0, 0.0, 1.0])
    omega = [np.zeros(3), np.zeros(3)]
    alpha = [np.zeros(3), np.zeros(3)]
    a_origin = [np.zeros(3), np.zeros(3)]

    a_origin[0] = -g
    print(f"\na_origin[0] = {a_origin[0]}")

    # For link 1 (qd=0, qdd=0)
    qd = np.zeros(1)
    qdd = np.zeros(1)

    z_1 = T1[:3, :3] @ z
    print(f"\nz_1 (joint axis): {z_1}")

    omega[1] = omega[0] + qd[0] * z_1
    print(f"omega[1] = {omega[1]} (qd={qd[0]})")

    alpha[1] = alpha[0] + qdd[0] * z_1 + np.cross(omega[0], qd[0] * z_1)
    print(f"alpha[1] = {alpha[1]} (qdd={qdd[0]})")

    r_1 = T1[:3, 3] - T0[:3, 3]
    print(f"\nr_1 (origin to origin): {r_1}")

    a_origin[1] = (
        a_origin[0] + np.cross(alpha[1], r_1) + np.cross(omega[1], np.cross(omega[1], r_1))
    )
    print(f"a_origin[1] = {a_origin[1]}")
    print(f"  = a_origin[0] + cross(alpha[1], r_1) + cross(omega[1], cross(omega[1], r_1))")
    print(
        f"  = {a_origin[0]} + {np.cross(alpha[1], r_1)} + {np.cross(omega[1], np.cross(omega[1], r_1))}"
    )

    # COM acceleration
    r_com = com_base - T0[:3, 3]
    print(f"\nr_com (origin to COM): {r_com}")
    a_com = a_origin[0] + np.cross(alpha[1], r_com) + np.cross(omega[1], np.cross(omega[1], r_com))
    print(f"a_com = {a_com}")
    print(f"  = a_origin[0] + cross(alpha[1], r_com) + cross(omega[1], cross(omega[1], r_com))")

    # Backward pass - forces
    print("\n[Backward Pass - Forces]")

    F = model.links[0].mass * a_com
    print(f"\nF (force at COM): {model.links[0].mass} * {a_com} = {F}")

    I_b = T1[:3, :3] @ model.links[0].inertia @ T1[:3, :3].T
    N = I_b @ alpha[1] + np.cross(omega[1], I_b @ omega[1])
    print(f"N (moment at COM): {N}")

    # Joint torque
    n_joint = np.cross(r_com, F) + N
    print(f"\nn_joint (moment about joint):")
    print(f"  = cross(r_com, F) + N")
    print(f"  = cross({r_com}, {F}) + {N}")
    print(f"  = {np.cross(r_com, F)} + {N}")
    print(f"  = {n_joint}")

    tau_manual = n_joint @ z_1
    print(f"\ntau = n_joint · z_1 = {n_joint} · {z_1} = {tau_manual:.6f}")

    # Analytical check
    print("\n[Analytical Check]")
    # For a pendulum, torque about joint = mg * perpendicular_distance
    # perpendicular_distance = L * sin(theta)
    perp_dist = model.links[0].com[0] * np.sin(theta)
    tau_analytical = model.links[0].mass * 9.81 * perp_dist
    print(f"Perpendicular distance: {model.links[0].com[0]} * sin({theta}) = {perp_dist:.6f} m")
    print(
        f"tau_analytical = m * g * d = {model.links[0].mass} * 9.81 * {perp_dist:.6f} = {tau_analytical:.6f} Nm"
    )

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Expected (analytical):  {expected:.6f} Nm")
    print(f"Computed (RNEA):         {tau[0]:.6f} Nm")
    print(f"Manual computation:      {tau_manual:.6f} Nm")
    print(f"\nDiscrepancy: {abs(tau[0] - expected) / expected * 100:.1f}%")

    # Check for common errors
    print("\n[Potential Issues]")
    if abs(abs(tau_manual) - abs(tau[0])) < 1e-6:
        print("✓ Manual RNEA matches solver computation")
    else:
        print("✗ Manual RNEA differs from solver!")

    # Check gravity sign
    if a_origin[0][0] > 0 and g[0] < 0:
        print("✓ Gravity direction looks correct (a_origin = -g)")
    else:
        print("✗ Check gravity direction!")

    # Check COM calculation
    expected_com = np.array(
        [model.links[0].com[0] * np.cos(theta), model.links[0].com[0] * np.sin(theta), 0]
    )
    if np.allclose(com_base[:2], expected_com[:2]):
        print("✓ COM position looks correct")
    else:
        print(f"✗ COM mismatch: expected {expected_com}, got {com_base}")

    # Check if 3x error
    if abs(abs(tau[0]) / expected - 3.0) < 0.1:
        print("\n⚠️  3x ERROR DETECTED!")
        print("   Possible causes:")
        print("   1. Double-counting of gravity")
        print("   2. Incorrect moment arm")
        print("   3. Sign error in acceleration")


if __name__ == "__main__":
    test_pendulum_debug()
