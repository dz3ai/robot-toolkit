#!/usr/bin/env python3
"""
Tutorial 2: Self-Collision Detection for Dual Arms

Challenge: "Self-collision risk" (challenges.md §2)

This tutorial demonstrates how to:
- Model robot links as collision primitives (capsules)
- Detect self-collision between dual arms
- Visualize collision points and distances
- Validate trajectory safety

Learning outcomes:
- Collision primitive modeling (capsules, spheres)
- Self-collision detection algorithms
- Real-time collision checking
- Contact point visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from robot_ik import six_dof_articulated, forward_kinematics
from robot_ik.collision import CollisionChecker, Sphere, Capsule, Box, CollisionResult, ContactPoint

import warnings

warnings.filterwarnings("ignore")


class DualArmCollisionChecker:
    """
    Collision checker for dual 6-DOF arms with primitive shapes.
    """

    def __init__(self, arm_offset=None, link_radius=0.05):
        """
        Initialize dual-arm collision checker.

        Args:
            arm_offset: Base position offset of arm2
            link_radius: Default radius for collision capsules
        """
        self.arm_offset = arm_offset if arm_offset is not None else np.array([1.5, 0, 0])
        self.link_radius = link_radius

        # Initialize robots
        self.arm1 = six_dof_articulated()
        self.arm2 = six_dof_articulated()
        self.arm2.base_tf[:3, 3] = self.arm_offset

        # Collision checker
        self.checker = CollisionChecker()

        # Link lengths (from six_dof_articulated)
        self.link_lengths = np.array([0.5, 0.4, 0.3, 0.2, 0.1, 0.05])

        # Build collision model
        self._build_collision_model()

    def _build_collision_model(self):
        """Add collision primitives for both arms."""
        # Arm1: capsules along each link
        for i in range(6):
            self.checker.add_shape(
                f"arm1_link{i}", Capsule(length=self.link_lengths[i], radius=self.link_radius)
            )

        # Arm2: capsules with base offset
        for i in range(6):
            self.checker.add_shape(
                f"arm2_link{i}",
                Capsule(
                    length=self.link_lengths[i],
                    radius=self.link_radius,
                    position=[self.arm_offset[0], self.arm_offset[1], self.arm_offset[2]],
                ),
            )

    def get_link_transforms(self, q):
        """
        Compute transformation matrices for all links.

        Args:
            q: Joint angles (6,)

        Returns:
            List of 4x4 transformation matrices
        """
        transforms = []
        current_tf = np.eye(4)

        for i in range(6):
            # Compute link transform (simplified DH)
            theta = q[i]
            d = self.link_lengths[i]

            # DH transform (simplified)
            c, s = np.cos(theta), np.sin(theta)
            tf_link = np.array([[c, -s, 0, d * c], [s, c, 0, d * s], [0, 0, 1, 0], [0, 0, 0, 1]])

            current_tf = current_tf @ tf_link
            transforms.append(current_tf.copy())

        return transforms

    def check_collision(self, q1, q2, check_self=True, check_mutual=True):
        """
        Check collision for dual-arm configuration.

        Args:
            q1: Joint angles for arm1
            q2: Joint angles for arm2
            check_self: Check self-collision within each arm
            check_mutual: Check collision between arms

        Returns:
            CollisionResult object
        """
        # Update collision primitive positions
        transforms1 = self.get_link_transforms(q1)
        transforms2 = self.get_link_transforms(q2)

        # Update arm1 link positions
        for i, tf in enumerate(transforms1):
            position = tf[:3, 3]
            self.checker.update_shape(f"arm1_link{i}", position=position)

        # Update arm2 link positions
        for i, tf in enumerate(transforms2):
            position = tf[:3, 3] + self.arm_offset
            self.checker.update_shape(f"arm2_link{i}", position=position)

        # Check collisions
        result = CollisionResult()

        # Self-collision (skip adjacent links)
        if check_self:
            for i in range(6):
                for j in range(i + 2, 6):  # Skip adjacent
                    collision = self.checker.check_pair_collision(f"arm1_link{i}", f"arm1_link{j}")
                    if collision.collided:
                        result.contacts.append(collision.contacts[0])
                        result.collided = True

            for i in range(6):
                for j in range(i + 2, 6):
                    collision = self.checker.check_pair_collision(f"arm2_link{i}", f"arm2_link{j}")
                    if collision.collided:
                        result.contacts.append(collision.contacts[0])
                        result.collided = True

        # Mutual collision between arms
        if check_mutual:
            for i in range(6):
                for j in range(6):
                    collision = self.checker.check_pair_collision(f"arm1_link{i}", f"arm2_link{j}")
                    if collision.collided:
                        result.contacts.append(collision.contacts[0])
                        result.collided = True

        return result


def visualize_collision(q1, q2, collision_result, arm_offset, title="Collision Detection"):
    """
    Visualize dual-arm configuration with collision points.

    Args:
        q1: Arm1 joint angles
        q2: Arm2 joint angles
        collision_result: Collision check result
        arm_offset: Arm2 base offset
        title: Plot title
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")

    # Compute forward kinematics
    arm1 = six_dof_articulated()
    arm2 = six_dof_articulated()
    arm2.base_tf[:3, 3] = arm_offset

    fk1 = forward_kinematics(arm1, q1)
    fk2 = forward_kinematics(arm2, q2)

    # Plot end-effector positions
    ax.scatter([fk1[0, 3]], [fk1[1, 3]], [fk1[2, 3]], c="blue", marker="o", s=100, label="Arm1 EE")
    ax.scatter([fk2[0, 3]], [fk2[1, 3]], [fk2[2, 3]], c="red", marker="o", s=100, label="Arm2 EE")

    # Plot base positions
    ax.scatter([0], [0], [0], c="blue", marker="^", s=200, label="Arm1 Base")
    ax.scatter(
        [arm_offset[0]],
        [arm_offset[1]],
        [arm_offset[2]],
        c="red",
        marker="^",
        s=200,
        label="Arm2 Base",
    )

    # Plot collision points
    if collision_result.collided:
        collision_points = np.array(
            [[c.position[0], c.position[1], c.position[2]] for c in collision_result.contacts]
        )
        ax.scatter(
            collision_points[:, 0],
            collision_points[:, 1],
            collision_points[:, 2],
            c="orange",
            marker="X",
            s=200,
            label=f"Collision ({len(collision_result.contacts)} points)",
        )

    # Labels
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")

    status = "COLLISION" if collision_result.collided else "Safe"
    color = "red" if collision_result.collided else "green"
    ax.set_title(f"{title}\nStatus: {status}", color=color, fontsize=14, fontweight="bold")
    ax.legend()

    plt.tight_layout()
    return fig


def generate_test_trajectory(n_steps=50):
    """
    Generate a test trajectory that moves arms towards each other.

    Args:
        n_steps: Number of trajectory steps

    Returns:
        traj1: List of arm1 configurations
        traj2: List of arm2 configurations
    """
    traj1 = []
    traj2 = []

    # Start: arms apart
    q1_start = np.array([0.1, 0.2, 0.1, 0.1, 0.1, 0.1])
    q2_start = np.array([0.1, -0.2, 0.1, 0.1, 0.1, 0.1])

    # End: arms converging
    q1_end = np.array([0.5, 0.8, 0.5, 0.5, 0.5, 0.5])
    q2_end = np.array([0.5, -0.8, 0.5, 0.5, 0.5, 0.5])

    for t in np.linspace(0, 1, n_steps):
        q1 = q1_start + t * (q1_end - q1_start)
        q2 = q2_start + t * (q2_end - q2_start)
        traj1.append(q1)
        traj2.append(q2)

    return traj1, traj2


def main():
    """Main tutorial execution."""
    print("=" * 60)
    print("Tutorial 2: Self-Collision Detection")
    print("=" * 60)

    # 1. Initialize collision checker
    print("\n[1] Initializing dual-arm collision checker...")
    checker = DualArmCollisionChecker(arm_offset=np.array([1.5, 0, 0]))
    print(f"   Arm2 offset: {checker.arm_offset}")
    print(f"   Link radius: {checker.link_radius} m")
    print(f"   Collision primitives: {12} capsules")

    # 2. Test safe configuration
    print("\n[2] Testing safe configuration...")
    q1_safe = np.array([0.1, 0.2, 0.1, 0.1, 0.1, 0.1])
    q2_safe = np.array([0.1, -0.2, 0.1, 0.1, 0.1, 0.1])

    result_safe = checker.check_collision(q1_safe, q2_safe)
    print(f"   Collision detected: {result_safe.collided}")
    print(f"   Contact points: {len(result_safe.contacts)}")

    # 3. Test collision configuration
    print("\n[3] Testing collision configuration...")
    q1_coll = np.array([1.2, 0.8, 0.5, 0.5, 0.5, 0.5])
    q2_coll = np.array([1.2, -0.8, 0.5, 0.5, 0.5, 0.5])

    result_coll = checker.check_collision(q1_coll, q2_coll)
    print(f"   Collision detected: {result_coll.collided}")
    print(f"   Contact points: {len(result_coll.contacts)}")

    if result_coll.collided:
        for i, contact in enumerate(result_coll.contacts):
            print(f"   Contact {i+1}: pos={contact.position}, depth={contact.depth:.3f}")

    # 4. Visualize safe configuration
    print("\n[4] Visualizing safe configuration...")
    fig_safe = visualize_collision(
        q1_safe, q2_safe, result_safe, checker.arm_offset, title="Safe Configuration"
    )
    fig_safe.savefig("tutorial02_collision_safe.png", dpi=150, bbox_inches="tight")
    print("   Saved: tutorial02_collision_safe.png")

    # 5. Visualize collision configuration
    print("\n[5] Visualizing collision configuration...")
    fig_coll = visualize_collision(
        q1_coll, q2_coll, result_coll, checker.arm_offset, title="Collision Configuration"
    )
    fig_coll.savefig("tutorial02_collision_collision.png", dpi=150, bbox_inches="tight")
    print("   Saved: tutorial02_collision_collision.png")

    # 6. Test trajectory safety
    print("\n[6] Testing trajectory safety...")
    traj1, traj2 = generate_test_trajectory(n_steps=30)

    collision_steps = []
    for i, (q1, q2) in enumerate(zip(traj1, traj2)):
        result = checker.check_collision(q1, q2)
        if result.collided:
            collision_steps.append(i)

    print(f"   Total steps: {len(traj1)}")
    print(f"   Collision steps: {len(collision_steps)}")

    if collision_steps:
        print(f"   First collision at step {collision_steps[0]}")
        print(f"   Collision rate: {len(collision_steps)/len(traj1)*100:.1f}%")

    # 7. Safety recommendation
    print("\n[7] Safety Recommendations")
    if len(collision_steps) > 0:
        print("   → Trajectory has collision points!")
        print("   → Use RRT* planner with collision checking")
        print("   → Add minimum distance constraint")
    else:
        print("   ✓ Trajectory is collision-free")

    print("\n" + "=" * 60)
    print("Tutorial 2 Complete!")
    print("=" * 60)

    plt.show()


if __name__ == "__main__":
    main()
