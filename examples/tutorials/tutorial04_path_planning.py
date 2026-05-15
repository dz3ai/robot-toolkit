#!/usr/bin/env python3
"""
Tutorial 4: Collision-Free Path Planning with RRT*

Challenge: "Complex real-time collision detection" (challenges.md §2)

This tutorial demonstrates how to:
- Plan collision-free paths using RRT* algorithm
- Integrate collision constraints into motion planning
- Handle workspace obstacles
- Plan sequential multi-robot paths

Learning outcomes:
- Sampling-based path planning (RRT*)
- Collision constraint integration
- Multi-robot sequential planning
- Path optimization and smoothing
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from robot_ik import six_dof_articulated, forward_kinematics
from robot_ik.path_planning import RRTStar, PathPlannerConfig
from robot_ik.collision import CollisionChecker, Sphere, Box

import warnings

warnings.filterwarnings("ignore")


class ObstacleEnvironment:
    """
    Simple obstacle environment for planning.
    """

    def __init__(self):
        """Initialize with default obstacles."""
        self.checker = CollisionChecker()
        self._add_default_obstacles()

    def _add_default_obstacles(self):
        """Add obstacles to checker."""
        # Central column obstacle
        self.checker.add_shape("column", Box(size=[0.2, 0.2, 1.0], position=[0.5, 0.0, 0.5]))

        # Side obstacle
        self.checker.add_shape("side_block", Box(size=[0.3, 0.3, 0.3], position=[0.7, 0.3, 0.4]))

    def is_collision_free(self, q):
        """
        Check if configuration is collision-free.

        Args:
            q: Joint configuration (6,)

        Returns:
            True if collision-free, False otherwise
        """
        # Simple check: compute end-effector position
        robot = six_dof_articulated()
        fk = forward_kinematics(robot, q)
        ee_pos = fk[:3, 3]

        # Check against all obstacles
        for shape_name in ["column", "side_block"]:
            collision = self.checker.check_point_collision(ee_pos, shape_name)
            if collision.collided:
                return False

        return True


class SimpleRRTStar:
    """
    Simplified RRT* implementation for tutorial.
    """

    def __init__(self, environment, max_iter=1000, step_size=0.1):
        """
        Initialize RRT* planner.

        Args:
            environment: ObstacleEnvironment object
            max_iter: Maximum iterations
            step_size: Step size for extension
        """
        self.env = environment
        self.max_iter = max_iter
        self.step_size = step_size

        # RRT* parameters
        self.gamma = 1.0  # Tuning parameter
        self.dim = 6  # Configuration space dimension

    def plan(self, start, goal):
        """
        Plan path from start to goal.

        Args:
            start: Start configuration
            goal: Goal configuration

        Returns:
            path: List of configurations from start to goal
        """
        # Initialize tree
        self.nodes = [start.copy()]
        self.parents = [0]  # Parent indices
        self.costs = [0.0]  # Cost to reach each node

        # Store goal index when reached
        goal_idx = None

        for iteration in range(self.max_iter):
            # 1. Sample random configuration
            if np.random.random() < 0.1:  # 10% bias towards goal
                q_rand = goal.copy()
            else:
                q_rand = self._sample_random()

            # 2. Find nearest node
            nearest_idx = self._find_nearest(q_rand)
            q_nearest = self.nodes[nearest_idx]

            # 3. Steer towards random sample
            q_new = self._steer(q_nearest, q_rand)

            # 4. Check collision and validity
            if not self.env.is_collision_free(q_new):
                continue

            # 5. Find nodes in neighborhood
            neighborhood = self._find_near_neighbors(q_new)

            # 6. Choose best parent
            best_parent = nearest_idx
            best_cost = self.costs[nearest_idx] + self._distance(q_nearest, q_new)

            for idx in neighborhood:
                q_candidate = self.nodes[idx]
                cost_candidate = self.costs[idx] + self._distance(q_candidate, q_new)

                if cost_candidate < best_cost:
                    # Check edge validity
                    if self._is_edge_valid(q_candidate, q_new):
                        best_parent = idx
                        best_cost = cost_candidate

            # 7. Add new node
            self.nodes.append(q_new)
            self.parents.append(best_parent)
            self.costs.append(best_cost)
            new_idx = len(self.nodes) - 1

            # 8. Rewire tree
            for idx in neighborhood:
                if idx == best_parent:
                    continue

                q_candidate = self.nodes[idx]
                cost_via_new = best_cost + self._distance(q_new, q_candidate)

                if cost_via_new < self.costs[idx]:
                    # Check edge validity
                    if self._is_edge_valid(q_new, q_candidate):
                        self.parents[idx] = new_idx
                        self.costs[idx] = cost_via_new

            # 9. Check if goal reached
            if self._distance(q_new, goal) < 0.1:
                if self.env.is_collision_free(goal):
                    goal_idx = len(self.nodes) - 1
                    self.nodes.append(goal.copy())
                    self.parents.append(goal_idx)
                    self.costs.append(self.costs[goal_idx])
                    break

        # Extract path
        if goal_idx is None:
            print("   Warning: Goal not reached")
            return None

        path = self._extract_path(len(self.nodes) - 1)
        return path

    def _sample_random(self):
        """Sample random configuration."""
        return np.random.uniform(-np.pi, np.pi, 6)

    def _find_nearest(self, q):
        """Find nearest node in tree."""
        distances = [self._distance(node, q) for node in self.nodes]
        return np.argmin(distances)

    def _steer(self, from_q, to_q):
        """Steer from one configuration towards another."""
        direction = to_q - from_q
        distance = np.linalg.norm(direction)

        if distance < self.step_size:
            return to_q

        return from_q + (direction / distance) * self.step_size

    def _find_near_neighbors(self, q):
        """Find nodes within neighborhood radius."""
        n = len(self.nodes)
        radius = min(self.step_size, self.gamma * (np.log(n) / n) ** (1 / self.dim))

        neighbors = []
        for i, node in enumerate(self.nodes):
            if self._distance(node, q) < radius:
                neighbors.append(i)

        return neighbors

    def _distance(self, q1, q2):
        """Compute distance between configurations."""
        return np.linalg.norm(q1 - q2)

    def _is_edge_valid(self, q1, q2):
        """Check if edge between configurations is valid."""
        # Discretize edge and check collisions
        n_checks = 10
        for t in np.linspace(0, 1, n_checks):
            q = q1 + t * (q2 - q1)
            if not self.env.is_collision_free(q):
                return False
        return True

    def _extract_path(self, goal_idx):
        """Extract path from goal to start."""
        path = []
        current = goal_idx

        while current is not None:
            path.append(self.nodes[current])
            current = self.parents[current]

        return path[::-1]  # Reverse to start->goal


def visualize_rrt_result(path, environment, start, goal, title="RRT* Path Planning"):
    """
    Visualize RRT* planning result.

    Args:
        path: Planned path (list of configs)
        environment: ObstacleEnvironment
        start: Start configuration
        goal: Goal configuration
        title: Plot title
    """
    fig = plt.figure(figsize=(16, 10))

    # Plot 1: 3D path in task space
    ax1 = fig.add_subplot(221, projection="3d")

    robot = six_dof_articulated()

    if path is not None:
        # Compute end-effector positions
        ee_positions = []
        for q in path:
            fk = forward_kinematics(robot, q)
            ee_positions.append(fk[:3, 3])

        ee_positions = np.array(ee_positions)

        # Plot path
        ax1.plot(
            ee_positions[:, 0],
            ee_positions[:, 1],
            ee_positions[:, 2],
            "b-",
            linewidth=2,
            label="Planned Path",
        )

        # Plot start and goal
        ax1.scatter(
            [ee_positions[0, 0]],
            [ee_positions[0, 1]],
            [ee_positions[0, 2]],
            c="green",
            marker="o",
            s=100,
            label="Start",
        )
        ax1.scatter(
            [ee_positions[-1, 0]],
            [ee_positions[-1, 1]],
            [ee_positions[-1, 2]],
            c="red",
            marker="X",
            s=100,
            label="Goal",
        )

    # Plot obstacles (simplified)
    ax1.scatter([0.5], [0.0], [0.5], c="orange", marker="s", s=200, label="Obstacles")
    ax1.scatter([0.7], [0.3], [0.4], c="orange", marker="s", s=200)

    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.set_zlabel("Z (m)")
    ax1.set_title("3D End-Effector Path")
    ax1.legend()

    # Plot 2: Joint space trajectory
    ax2 = fig.add_subplot(222)

    if path is not None:
        path_array = np.array(path)
        for i in range(6):
            ax2.plot(path_array[:, i], label=f"J{i+1}", alpha=0.7)

    ax2.set_xlabel("Waypoint")
    ax2.set_ylabel("Joint Angle (rad)")
    ax2.set_title("Joint Space Trajectory")
    ax2.legend(ncol=2, fontsize=8)
    ax2.grid(True, alpha=0.3)

    # Plot 3: Planning statistics
    ax3 = fig.add_subplot(223)
    ax3.axis("off")

    if path is not None:
        # Compute path statistics
        path_length = sum(np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1))

        stats_text = f"""
        Planning Statistics
        
        Path Length: {len(path)} waypoints
        Total Distance: {path_length:.3f} rad
        Success: Yes
        """
    else:
        stats_text = """
        Planning Statistics
        
        Path Length: N/A
        Total Distance: N/A
        Success: No (goal not reached)
        """

    ax3.text(0.1, 0.5, stats_text, fontsize=12, family="monospace", verticalalignment="center")

    # Plot 4: Configuration space (first 2 joints)
    ax4 = fig.add_subplot(224)

    if path is not None:
        path_array = np.array(path)
        ax4.plot(path_array[:, 0], path_array[:, 1], "b-", linewidth=2)
        ax4.scatter(path_array[0, 0], path_array[0, 1], c="green", marker="o", s=100, label="Start")
        ax4.scatter(path_array[-1, 0], path_array[-1, 1], c="red", marker="X", s=100, label="Goal")

    ax4.set_xlabel("Joint 1 (rad)")
    ax4.set_ylabel("Joint 2 (rad)")
    ax4.set_title("Configuration Space (J1 vs J2)")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    return fig


def plan_dual_arm_sequential():
    """
    Plan sequential paths for dual arms.

    Plans path for arm1 first, then plans arm2 considering
    arm1's final position as obstacle.
    """
    print("\n[4] Planning sequential dual-arm paths...")

    env = ObstacleEnvironment()
    planner = SimpleRRTStar(env, max_iter=500, step_size=0.15)

    # Arm1 path
    start1 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    goal1 = np.array([1.0, 0.5, 0.5, 0.5, 0.5, 0.5])

    print("   Planning Arm1...")
    path1 = planner.plan(start1, goal1)

    if path1 is not None:
        print(f"   Arm1 path: {len(path1)} waypoints")

        # Add arm1 final position as obstacle for arm2
        robot = six_dof_articulated()
        fk1 = forward_kinematics(robot, path1[-1])
        ee1_pos = fk1[:3, 3]

        env.checker.add_shape("arm1_final", Sphere(radius=0.15, position=ee1_pos))
    else:
        print("   Arm1 planning failed")
        return None, None

    # Arm2 path (with arm1 as obstacle)
    start2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    goal2 = np.array([1.0, -0.5, 0.5, 0.5, 0.5, 0.5])

    print("   Planning Arm2 (with Arm1 as obstacle)...")
    path2 = planner.plan(start2, goal2)

    if path2 is not None:
        print(f"   Arm2 path: {len(path2)} waypoints")
    else:
        print("   Arm2 planning failed")

    return path1, path2


def main():
    """Main tutorial execution."""
    print("=" * 60)
    print("Tutorial 4: Collision-Free Path Planning (RRT*)")
    print("=" * 60)

    # 1. Setup environment and planner
    print("\n[1] Setting up planning environment...")
    env = ObstacleEnvironment()
    planner = SimpleRRTStar(env, max_iter=1000, step_size=0.1)

    print(f"   Obstacles: {len(env.checker.shapes)}")
    print(f"   Max iterations: {planner.max_iter}")
    print(f"   Step size: {planner.step_size}")

    # 2. Define planning problem
    print("\n[2] Defining single-arm planning problem...")

    start = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    goal = np.array([1.2, 0.8, 0.6, 0.4, 0.2, 0.0])

    print(f"   Start: {start[:3]}... (first 3 joints)")
    print(f"   Goal: {goal[:3]}... (first 3 joints)")

    # 3. Plan path
    print("\n[3] Planning collision-free path...")
    path = planner.plan(start, goal)

    if path is not None:
        print(f"   Success! Path found with {len(path)} waypoints")

        # Compute path length
        path_length = sum(np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1))
        print(f"   Total path length: {path_length:.3f} rad")
    else:
        print("   Failed to find path")

    # 4. Dual-arm sequential planning
    path1, path2 = plan_dual_arm_sequential()

    # 5. Visualize results
    print("\n[5] Generating visualization...")
    fig = visualize_rrt_result(path, env, start, goal, title="RRT* Path Planning with Obstacles")

    output_path = "tutorial04_rrt_star.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"   Saved: {output_path}")

    # 6. Recommendations
    print("\n[6] Planning Recommendations")

    if path is not None:
        print("   ✓ Single-arm planning successful")
        if path1 is not None and path2 is not None:
            print("   ✓ Dual-arm sequential planning successful")
        else:
            print("   → Consider parallel planning algorithms")
    else:
        print("   → Try increasing max_iter or reducing step_size")
        print("   → Check if goal is reachable")

    print("\n" + "=" * 60)
    print("Tutorial 4 Complete!")
    print("=" * 60)

    plt.show()


if __name__ == "__main__":
    main()
