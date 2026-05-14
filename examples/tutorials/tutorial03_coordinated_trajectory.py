#!/usr/bin/env python3
"""
Tutorial 3: Coordinated Trajectory Planning for Dual Arms

Challenge: "Synchronized trajectory planning" (challenges.md §3)

This tutorial demonstrates how to:
- Generate time-synchronized trajectories for dual arms
- Use waypoint interpolation with smooth velocity profiles
- Coordinate motion for shared object manipulation
- Validate temporal alignment between arms

Learning outcomes:
- Multi-waypoint trajectory generation
- S-curve velocity profiling for smooth motion
- Dual-arm temporal coordination
- Trajectory timing validation
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from robot_ik import six_dof_articulated, forward_kinematics
from robot_ik.trajectory import (
    waypoint_trajectory, s_curve_profile, trapezoidal_profile,
    interpolate_cubic, interpolate_quintic
)

import warnings
warnings.filterwarnings('ignore')


class CoordinatedTrajectory:
    """
    Time-synchronized dual-arm trajectory.
    """
    
    def __init__(self, traj1, traj2, times):
        """
        Initialize coordinated trajectory.
        
        Args:
            traj1: Arm1 trajectory (list of configurations)
            traj2: Arm2 trajectory (list of configurations)
            times: Time points for trajectory
        """
        self.traj1 = np.array(traj1)
        self.traj2 = np.array(traj2)
        self.times = np.array(times)
        
        # Validate temporal alignment
        assert len(traj1) == len(traj2) == len(times), \
            "Trajectories must have same length"
    
    def validate_synchronization(self, tolerance=1e-6):
        """
        Validate temporal alignment between trajectories.
        
        Args:
            tolerance: Maximum allowed time difference
        
        Returns:
            is_synced: Boolean indicating synchronization
        """
        # Check if time points are unique and monotonic
        unique_times = np.unique(self.times)
        if len(unique_times) != len(self.times):
            return False
        
        # Check monotonic increasing
        if not np.all(np.diff(self.times) > 0):
            return False
        
        return True
    
    def get_configuration_at(self, t, arm=1):
        """
        Get configuration at time t using interpolation.
        
        Args:
            t: Time to query
            arm: Arm number (1 or 2)
        
        Returns:
            Configuration at time t
        """
        if t < self.times[0] or t > self.times[-1]:
            raise ValueError(f"Time {t} outside trajectory range")
        
        traj = self.traj1 if arm == 1 else self.traj2
        
        # Linear interpolation
        idx = np.searchsorted(self.times, t)
        if idx == 0:
            return traj[0]
        if idx == len(self.times):
            return traj[-1]
        
        t0, t1 = self.times[idx-1], self.times[idx]
        alpha = (t - t0) / (t1 - t0)
        
        q = traj[idx-1] + alpha * (traj[idx] - traj[idx-1])
        return q


def generate_pick_and_place_trajectory(
    pick_pose, place_pose,
    gripper_offset,
    duration=3.0,
    n_waypoints=10
):
    """
    Generate pick-and-place trajectory for dual arms.
    
    Args:
        pick_pose: Pick pose [x, y, z, rx, ry, rz]
        place_pose: Place pose [x, y, z, rx, ry, rz]
        gripper_offset: Offset between grippers [x, y, z, rx, ry, rz]
        duration: Total trajectory duration (seconds)
        n_waypoints: Number of waypoints
    
    Returns:
        CoordinatedTrajectory object
    """
    # Generate waypoints (pick → place)
    waypoints = []
    for t in np.linspace(0, 1, n_waypoints):
        wp = pick_pose + t * (place_pose - pick_pose)
        waypoints.append(wp)
    
    # Arm1 trajectory (leading)
    traj1_waypoints = waypoints
    times = np.linspace(0, duration, n_waypoints)
    
    # Generate trajectory with S-curve velocity
    traj1 = waypoint_trajectory(
        traj1_waypoints,
        times,
        profile_type="s-curve"
    )
    
    # Arm2 trajectory (synchronized, with gripper offset)
    traj2_waypoints = [wp + gripper_offset for wp in waypoints]
    traj2 = waypoint_trajectory(
        traj2_waypoints,
        times,
        profile_type="s-curve"
    )
    
    # Sample trajectories at common times
    sample_times = np.linspace(0, duration, 100)
    q1_samples = [traj1.get_configuration_at(t) for t in sample_times]
    q2_samples = [traj2.get_configuration_at(t) for t in sample_times]
    
    return CoordinatedTrajectory(q1_samples, q2_samples, sample_times)


def visualize_coordinated_trajectory(
    traj, arm_offset,
    title="Coordinated Dual-Arm Trajectory"
):
    """
    Visualize coordinated trajectory.
    
    Args:
        traj: CoordinatedTrajectory object
        arm_offset: Arm2 base offset
        title: Plot title
    """
    fig = plt.figure(figsize=(16, 10))
    
    # Plot 1: 3D end-effector paths
    ax1 = fig.add_subplot(221, projection='3d')
    
    # Compute end-effector positions
    arm1 = six_dof_articulated()
    arm2 = six_dof_articulated()
    arm2.base_tf[:3, 3] = arm_offset
    
    ee_pos1 = []
    ee_pos2 = []
    
    for i in range(len(traj.times)):
        fk1 = forward_kinematics(arm1, traj.traj1[i])
        fk2 = forward_kinematics(arm2, traj.traj2[i])
        ee_pos1.append(fk1[:3, 3])
        ee_pos2.append(fk2[:3, 3])
    
    ee_pos1 = np.array(ee_pos1)
    ee_pos2 = np.array(ee_pos2)
    
    # Plot trajectories
    ax1.plot(ee_pos1[:, 0], ee_pos1[:, 1], ee_pos1[:, 2],
             'b-', linewidth=2, label='Arm1 Path')
    ax1.plot(ee_pos2[:, 0], ee_pos2[:, 1], ee_pos2[:, 2],
             'r-', linewidth=2, label='Arm2 Path')
    
    # Plot start and end
    ax1.scatter(ee_pos1[0, 0], ee_pos1[0, 1], ee_pos1[0, 2],
                c='green', marker='o', s=100, label='Start')
    ax1.scatter(ee_pos1[-1, 0], ee_pos1[-1, 1], ee_pos1[-1, 2],
                c='orange', marker='X', s=100, label='End')
    
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Z (m)')
    ax1.set_title('End-Effector Paths')
    ax1.legend()
    
    # Plot 2: Joint angles over time
    ax2 = fig.add_subplot(222)
    
    for i in range(6):
        ax2.plot(traj.times, traj.traj1[:, i], 
                 label=f'J{i+1}', alpha=0.7)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Joint Angle (rad)')
    ax2.set_title('Arm1 Joint Angles')
    ax2.legend(ncol=2, fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Joint velocities
    ax3 = fig.add_subplot(223)
    
    # Compute velocities
    dt = np.diff(traj.times)
    vel1 = np.diff(traj.traj1, axis=0) / dt[:, np.newaxis]
    
    for i in range(6):
        ax3.plot(traj.times[:-1], vel1[:, i],
                 label=f'J{i+1}', alpha=0.7)
    
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Joint Velocity (rad/s)')
    ax3.set_title('Arm1 Joint Velocities')
    ax3.legend(ncol=2, fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Temporal alignment
    ax4 = fig.add_subplot(224)
    
    # Plot gripper distance over time
    gripper_dist = np.linalg.norm(ee_pos1 - ee_pos2, axis=1)
    ax4.plot(traj.times, gripper_dist, 'g-', linewidth=2)
    ax4.axhline(y=0.6, color='r', linestyle='--', label='Target (0.6m)')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Gripper Distance (m)')
    ax4.set_title('Gripper Separation')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig


def main():
    """Main tutorial execution."""
    print("=" * 60)
    print("Tutorial 3: Coordinated Trajectory Planning")
    print("=" * 60)
    
    # 1. Define pick-and-place task
    print("\n[1] Defining pick-and-place task...")
    
    pick_pose = np.array([0.5, 0.3, 0.4, 0, 0, 0])
    place_pose = np.array([0.5, -0.3, 0.4, 0, 0, 0])
    gripper_offset = np.array([0, 0.6, 0, 0, 0, 0])  # 0.6m separation
    
    print(f"   Pick pose: {pick_pose}")
    print(f"   Place pose: {place_pose}")
    print(f"   Gripper offset: {gripper_offset[:3]} m")
    
    # 2. Generate coordinated trajectory
    print("\n[2] Generating coordinated trajectory...")
    
    traj = generate_pick_and_place_trajectory(
        pick_pose, place_pose, gripper_offset,
        duration=3.0, n_waypoints=8
    )
    
    print(f"   Duration: {traj.times[-1]:.2f} s")
    print(f"   Waypoints: {len(traj.times)}")
    print(f"   Sample rate: {1/np.mean(np.diff(traj.times)):.1f} Hz")
    
    # 3. Validate synchronization
    print("\n[3] Validating temporal synchronization...")
    
    is_synced = traj.validate_synchronization()
    print(f"   Synchronized: {is_synced}")
    
    # Check time alignment
    time_diffs = np.diff(traj.times)
    print(f"   Min dt: {np.min(time_diffs):.4f} s")
    print(f"   Max dt: {np.max(time_diffs):.4f} s")
    print(f"   Mean dt: {np.mean(time_diffs):.4f} s")
    
    # 4. Analyze trajectory smoothness
    print("\n[4] Analyzing trajectory smoothness...")
    
    # Compute velocities
    dt = np.diff(traj.times)
    vel1 = np.diff(traj.traj1, axis=0) / dt[:, np.newaxis]
    vel2 = np.diff(traj.traj2, axis=0) / dt[:, np.newaxis]
    
    max_vel1 = np.max(np.abs(vel1))
    max_vel2 = np.max(np.abs(vel2))
    
    print(f"   Arm1 max velocity: {max_vel1:.3f} rad/s")
    print(f"   Arm2 max velocity: {max_vel2:.3f} rad/s")
    
    # Compute accelerations
    acc1 = np.diff(vel1, axis=0) / dt[:-1, np.newaxis]
    max_acc1 = np.max(np.abs(acc1))
    
    print(f"   Arm1 max acceleration: {max_acc1:.3f} rad/s²")
    
    # 5. Validate gripper constraint
    print("\n[5] Validating gripper distance constraint...")
    
    arm1 = six_dof_articulated()
    arm2 = six_dof_articulated()
    arm2.base_tf[:3, 3] = np.array([1.5, 0, 0])
    
    distances = []
    for i in range(len(traj.times)):
        fk1 = forward_kinematics(arm1, traj.traj1[i])
        fk2 = forward_kinematics(arm2, traj.traj2[i])
        dist = np.linalg.norm(fk1[:3, 3] - fk2[:3, 3])
        distances.append(dist)
    
    distances = np.array(distances)
    target_dist = 0.6
    error = np.abs(distances - target_dist)
    
    print(f"   Target distance: {target_dist:.3f} m")
    print(f"   Mean distance: {np.mean(distances):.3f} m")
    print(f"   Max error: {np.max(error):.4f} m")
    print(f"   RMS error: {np.sqrt(np.mean(error**2)):.4f} m")
    
    # 6. Visualize trajectory
    print("\n[6] Generating trajectory visualization...")
    
    fig = visualize_coordinated_trajectory(
        traj, np.array([1.5, 0, 0]),
        title="Coordinated Pick-and-Place (3s)"
    )
    
    output_path = "tutorial03_trajectory.png"
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"   Saved: {output_path}")
    
    # 7. Recommendations
    print("\n[7] Trajectory Quality Assessment")
    
    if max_vel1 < 2.0 and max_vel2 < 2.0:
        print("   ✓ Velocities within safe limits")
    else:
        print("   → Warning: High velocities detected")
    
    if max_acc1 < 5.0:
        print("   ✓ Accelerations within smooth range")
    else:
        print("   → Warning: High accelerations detected")
    
    if np.max(error) < 0.01:
        print("   ✓ Gripper constraint well maintained")
    else:
        print("   → Consider closed-chain constraint control")
    
    print("\n" + "=" * 60)
    print("Tutorial 3 Complete!")
    print("=" * 60)
    
    plt.show()


if __name__ == "__main__":
    main()
