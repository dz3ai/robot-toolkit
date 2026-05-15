#!/usr/bin/env python3
"""
Tutorial 1: Dual-Arm Workspace Analysis

Challenge: "Limited usable shared workspace" (challenges.md §1)

This tutorial demonstrates how to:
- Sample the reachable workspace of dual 6-DOF manipulators
- Visualize workspace overlap with matplotlib
- Calculate shared workspace volume
- Analyze dual-arm configuration impact

Learning outcomes:
- Forward kinematics for workspace sampling
- 3D visualization techniques
- Workspace intersection analysis
- Dual-arm coordinate transforms
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from robot_ik import six_dof_articulated, forward_kinematics

# Suppress matplotlib warnings
import warnings

warnings.filterwarnings("ignore")


def sample_workspace(robot_model, n_samples=2000, joint_limits=None):
    """
    Sample reachable workspace points using random joint configurations.

    Args:
        robot_model: Robot model with forward kinematics
        n_samples: Number of random configurations to sample
        joint_limits: List of (min, max) for each joint (default: -pi to pi)

    Returns:
        points: Nx3 array of end-effector positions
        configs: Nx6 array of joint configurations (for IK later)
    """
    if joint_limits is None:
        joint_limits = [(-np.pi, np.pi)] * 6

    points = []
    configs = []

    for _ in range(n_samples):
        # Sample random joint angles
        q = np.random.uniform(
            low=[l[0] for l in joint_limits], high=[l[1] for l in joint_limits], size=6
        )

        # Compute forward kinematics
        try:
            fk_result = forward_kinematics(robot_model, q)
            position = fk_result[:3, 3]  # Extract position
            points.append(position)
            configs.append(q)
        except Exception as e:
            # Skip invalid configurations
            continue

    return np.array(points), np.array(configs)


def compute_workspace_overlap(points1, points2, voxel_size=0.05):
    """
    Compute overlap between two workspaces using voxel grid.

    Args:
        points1: Nx3 array of workspace points for arm1
        points2: Mx3 array of workspace points for arm2
        voxel_size: Size of voxel grid for discretization

    Returns:
        volume_overlap: Estimated overlap volume (m³)
        volume1: Total workspace volume for arm1
        volume2: Total workspace volume for arm2
        overlap_ratio: Overlap / min(volume1, volume2)
    """
    # Create voxel grids
    all_points = np.vstack([points1, points2])
    bounds_min = np.min(all_points, axis=0)
    bounds_max = np.max(all_points, axis=0)

    # Discretize space into voxels
    grid_shape = np.ceil((bounds_max - bounds_min) / voxel_size).astype(int)

    def voxelize(points):
        indices = ((points - bounds_min) / voxel_size).astype(int)
        # Clamp to grid bounds
        indices = np.clip(indices, [0, 0, 0], grid_shape - 1)
        # Flatten to 1D indices
        flat_indices = (
            indices[:, 0] * grid_shape[1] * grid_shape[2]
            + indices[:, 1] * grid_shape[2]
            + indices[:, 2]
        )
        return set(flat_indices)

    voxels1 = voxelize(points1)
    voxels2 = voxelize(points2)

    # Count voxels
    n_voxels1 = len(voxels1)
    n_voxels2 = len(voxels2)
    n_overlap = len(voxels1 & voxels2)

    # Compute volumes (voxel count * voxel volume)
    voxel_volume = voxel_size**3
    volume1 = n_voxels1 * voxel_volume
    volume2 = n_voxels2 * voxel_volume
    volume_overlap = n_overlap * voxel_volume

    overlap_ratio = volume_overlap / min(volume1, volume2) if min(volume1, volume2) > 0 else 0

    return volume_overlap, volume1, volume2, overlap_ratio


def visualize_dual_workspace(points1, points2, arm_offset, title="Dual-Arm Workspace"):
    """
    Visualize dual-arm workspace with overlap region.

    Args:
        points1: Workspace points for arm1
        points2: Workspace points for arm2
        arm_offset: Base offset of arm2 (for plot labels)
        title: Plot title
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")

    # Plot workspace clouds (subsample for performance)
    n_plot = min(500, len(points1))
    idx1 = np.random.choice(len(points1), n_plot, replace=False)
    idx2 = np.random.choice(len(points2), n_plot, replace=False)

    # Arm1 workspace (blue)
    ax.scatter(
        points1[idx1, 0],
        points1[idx1, 1],
        points1[idx1, 2],
        c="blue",
        alpha=0.15,
        s=10,
        label="Arm1 Workspace",
    )

    # Arm2 workspace (red)
    ax.scatter(
        points2[idx2, 0],
        points2[idx2, 1],
        points2[idx2, 2],
        c="red",
        alpha=0.15,
        s=10,
        label="Arm2 Workspace",
    )

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

    # Compute and plot overlap statistics
    volume_overlap, vol1, vol2, ratio = compute_workspace_overlap(points1, points2)

    # Labels and formatting
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title(f"{title}\nOverlap: {volume_overlap:.3f} m³ ({ratio*100:.1f}%)")
    ax.legend()

    # Equal aspect ratio
    max_range = (
        np.array(
            [
                points1[:, 0].max() - points1[:, 0].min(),
                points1[:, 1].max() - points1[:, 1].min(),
                points1[:, 2].max() - points1[:, 2].min(),
            ]
        ).max()
        / 2.0
    )

    mid_x = (points1[:, 0].max() + points1[:, 0].min()) * 0.5
    mid_y = (points1[:, 1].max() + points1[:, 1].min()) * 0.5
    mid_z = (points1[:, 2].max() + points1[:, 2].min()) * 0.5

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    plt.tight_layout()
    return fig


def main():
    """Main tutorial execution."""
    print("=" * 60)
    print("Tutorial 1: Dual-Arm Workspace Analysis")
    print("=" * 60)

    # 1. Setup dual-arm configuration
    print("\n[1] Setting up dual 6-DOF manipulators...")

    arm1 = six_dof_articulated()
    arm2 = six_dof_articulated()

    # Configure arm2 base offset (1.5m to the right)
    arm2_offset = np.array([1.5, 0.0, 0.0])
    arm2.base_tf[:3, 3] = arm2_offset

    print(f"   Arm1 base: [0.0, 0.0, 0.0]")
    print(f"   Arm2 base: [{arm2_offset[0]}, {arm2_offset[1]}, {arm2_offset[2]}]")

    # 2. Sample workspace points
    print("\n[2] Sampling workspace points...")
    n_samples = 1000

    points1, configs1 = sample_workspace(arm1, n_samples=n_samples)
    print(f"   Arm1: {len(points1)} valid samples")

    points2, configs2 = sample_workspace(arm2, n_samples=n_samples)
    print(f"   Arm2: {len(points2)} valid samples")

    # 3. Compute workspace overlap
    print("\n[3] Computing workspace overlap...")
    volume_overlap, vol1, vol2, overlap_ratio = compute_workspace_overlap(
        points1, points2, voxel_size=0.05
    )

    print(f"   Arm1 workspace volume: {vol1:.3f} m³")
    print(f"   Arm2 workspace volume: {vol2:.3f} m³")
    print(f"   Overlap volume: {volume_overlap:.3f} m³")
    print(f"   Overlap ratio: {overlap_ratio*100:.1f}%")

    # 4. Visualize workspace
    print("\n[4] Generating visualization...")
    fig = visualize_dual_workspace(
        points1, points2, arm2_offset, title="Dual-Arm Workspace (1.5m Offset)"
    )

    output_path = "tutorial01_workspace.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"   Saved: {output_path}")

    # 5. Analyze configuration impact
    print("\n[5] Analyzing different arm offsets...")
    offsets = [1.0, 1.5, 2.0, 2.5]

    print(f"   {'Offset':<8} {'Overlap (m³)':<15} {'Ratio (%)':<12}")
    print(f"   {'-'*8} {'-'*15} {'-'*12}")

    for offset in offsets:
        arm2_test = six_dof_articulated()
        arm2_test.base_tf[:3, 3] = np.array([offset, 0.0, 0.0])

        points2_test, _ = sample_workspace(arm2_test, n_samples=n_samples)
        vol_ov, _, _, ratio = compute_workspace_overlap(points1, points2_test)

        print(f"   {offset:<8.1f} {vol_ov:<15.3f} {ratio*100:<12.1f}")

    # 6. Task planning recommendation
    print("\n[6] Task Planning Recommendation")
    if overlap_ratio > 0.3:
        print("   ✓ Excellent overlap for cooperative tasks")
        print("   → Recommend for assembly, dual-arm manipulation")
    elif overlap_ratio > 0.1:
        print("   → Moderate overlap suitable for handover tasks")
    else:
        print("   → Limited overlap, consider reducing arm offset")

    print("\n" + "=" * 60)
    print("Tutorial 1 Complete!")
    print("=" * 60)

    # Show plot
    plt.show()


if __name__ == "__main__":
    main()
