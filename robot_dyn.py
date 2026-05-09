
"""robot-dyn — Rigid Body Dynamics Solver

Recursive Newton-Euler inverse dynamics and composite-rigid-body
forward dynamics for serial manipulators. Builds on robot-ik's
DH parameter infrastructure.

Author: Danny Zeng
License: MIT
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class LinkInertia:
    """Mass/inertia properties of a single robot link."""
    mass: float                    # kg
    com: np.ndarray                # center of mass in link frame (3,)
    inertia: np.ndarray            # 3x3 inertia tensor about COM (kg*m^2)


@dataclass
class RobotDynamicsModel:
    """DH parameters + inertia for dynamics computation."""
    dh_a: np.ndarray               # link length (6,)
    dh_alpha: np.ndarray           # link twist (6,)
    dh_d: np.ndarray               # link offset (6,)
    links: List[LinkInertia]       # one per link (6)
    gravity: np.ndarray            # gravity vector in base frame (3,), default [0,0,-9.81]
    joint_damping: np.ndarray      # viscous damping per joint (6,), default zeros


def six_dof_articulated_dyn() -> RobotDynamicsModel:
    """Standard 6-DOF articulated robot with realistic mass parameters."""
    return RobotDynamicsModel(
        dh_a=np.array([0, 0.5, 0.1, 0, 0, 0]),
        dh_alpha=np.array([-np.pi/2, 0, -np.pi/2, np.pi/2, -np.pi/2, 0]),
        dh_d=np.array([0.3, 0, 0, 0.4, 0, 0.1]),
        links=[
            LinkInertia(mass=2.0, com=np.array([0.0, 0.0, 0.15]),
                       inertia=np.array([[0.01, 0, 0], [0, 0.01, 0], [0, 0, 0.005]])),
            LinkInertia(mass=3.0, com=np.array([0.25, 0.0, 0.0]),
                       inertia=np.array([[0.02, 0, 0], [0, 0.15, 0], [0, 0, 0.15]])),
            LinkInertia(mass=2.0, com=np.array([0.05, 0.0, 0.0]),
                       inertia=np.array([[0.01, 0, 0], [0, 0.08, 0], [0, 0, 0.08]])),
            LinkInertia(mass=1.5, com=np.array([0.0, 0.0, 0.2]),
                       inertia=np.array([[0.005, 0, 0], [0, 0.005, 0], [0, 0, 0.003]])),
            LinkInertia(mass=0.8, com=np.array([0.0, 0.0, 0.0]),
                       inertia=np.array([[0.002, 0, 0], [0, 0.002, 0], [0, 0, 0.001]])),
            LinkInertia(mass=0.3, com=np.array([0.0, 0.0, 0.05]),
                       inertia=np.array([[0.001, 0, 0], [0, 0.001, 0], [0, 0, 0.0005]])),
        ],
        gravity=np.array([0.0, 0.0, -9.81]),
        joint_damping=np.zeros(6),
    )


class DynamicsSolver:
    """Rigid body dynamics for serial manipulators.

    Uses recursive Newton-Euler (inverse dynamics) and
    composite-rigid-body algorithm (forward dynamics).
    """

    def __init__(self, model: RobotDynamicsModel):
        self.model = model
        self.n = len(model.links)

    def _dh_transform(self, a, alpha, d, theta) -> np.ndarray:
        """4x4 DH homogeneous transform using standard convention."""
        ct, st = np.cos(theta), np.sin(theta)
        ca, sa = np.cos(alpha), np.sin(alpha)
        return np.array([
            [ct, -st*ca,  st*sa, a*ct],
            [st,  ct*ca, -ct*sa, a*st],
            [0,      sa,     ca,    d],
            [0,       0,      0,    1],
        ])

    def forward_kinematics_all(self, q: np.ndarray) -> List[np.ndarray]:
        """Compute all link transforms (base to each frame). Returns list of 4x4."""
        T = np.eye(4)
        Ts = [T.copy()]
        for i in range(self.n):
            T = T @ self._dh_transform(
                self.model.dh_a[i], self.model.dh_alpha[i],
                self.model.dh_d[i], q[i])
            Ts.append(T.copy())
        return Ts

    def inverse_dynamics(
        self,
        q: np.ndarray,
        qd: np.ndarray,
        qdd: np.ndarray,
        external_wrench: Optional[np.ndarray] = None,  # (6,) at end-effector
    ) -> np.ndarray:
        """Recursive Newton-Euler inverse dynamics.

        Given joint positions, velocities, accelerations, compute joint torques.

        Args:
            q: joint positions (6,)
            qd: joint velocities (6,)
            qdd: joint accelerations (6,)
            external_wrench: optional (fx,fy,fz,tx,ty,tz) at end-effector

        Returns:
            tau: joint torques (6,)
        """
        Ts = self.forward_kinematics_all(q)
        g = self.model.gravity

        # Forward recursion: compute velocities and accelerations
        omega = [np.zeros(3)]  # link i angular velocity in link i frame
        alpha = [np.zeros(3)]  # link i angular acceleration
        a_lin = [g.copy()]     # base acceleration = -gravity (Newton's law)
        a_com = [np.zeros(3)]  # link i linear acceleration of COM

        for i in range(self.n):
            R_prev = Ts[i][:3, :3].T  # rotation from base to link i
            z = np.array([0, 0, 1])

            # Angular velocity
            w = R_prev @ omega[i] + qd[i] * z
            omega.append(w)

            # Angular acceleration
            al = R_prev @ alpha[i] + qdd[i] * z + np.cross(R_prev @ omega[i], qd[i] * z)
            alpha.append(al)

            # Linear acceleration of origin
            p_prev = Ts[i+1][:3, 3] - Ts[i][:3, 3]  # vector from link i to i+1 in base
            a = R_prev @ a_lin[i] + np.cross(alpha[i+1], p_prev) + np.cross(omega[i+1], np.cross(omega[i+1], p_prev))
            a_lin.append(a)

            # Linear acceleration of COM
            com = self.model.links[i].com
            ac = a + np.cross(alpha[i+1], com) + np.cross(omega[i+1], np.cross(omega[i+1], com))
            a_com.append(ac)

        # Backward recursion: compute forces and torques
        f = np.zeros(3)   # force exerted on link i by link i-1
        n = np.zeros(3)   # torque exerted on link i by link i-1
        tau = np.zeros(self.n)

        for i in range(self.n - 1, -1, -1):
            R_next = Ts[i+1][:3, :3]

            # Force balance
            m = self.model.links[i].mass
            I = self.model.links[i].inertia
            com_link = self.model.links[i].com

            # Transform COM from link frame to base frame
            R_link = Ts[i+1][:3, :3]
            com_base = R_link @ com_link

            F = m * a_com[i+1]
            N = I @ alpha[i+1] + np.cross(omega[i+1], I @ omega[i+1])

            f_prev = R_next @ f + F
            n_prev = (R_next @ n +
                      np.cross(com_base, F) +
                      np.cross(Ts[i+1][:3, 3] - Ts[i][:3, 3], R_next @ f) +
                      N)

            f = f_prev
            n = n_prev

            # Joint torque (projection onto z-axis of joint i)
            z = np.array([0, 0, 1])
            tau[i] = n @ (Ts[i+1][:3, :3].T @ z).flatten()

            # Add gravity compensation (done via acceleration already)
            # Add joint damping
            tau[i] += self.model.joint_damping[i] * qd[i]

            # Add external wrench if at last link
            if i == self.n - 1 and external_wrench is not None:
                tau[i] += external_wrench[3:6] @ (Ts[i+1][:3, :3].T @ z).flatten()

        return tau

    def gravity_torque(self, q: np.ndarray) -> np.ndarray:
        """Compute gravity compensation torques (qd=0, qdd=0)."""
        return self.inverse_dynamics(q, np.zeros(self.n), np.zeros(self.n))

    def coriolis_torque(self, q: np.ndarray, qd: np.ndarray) -> np.ndarray:
        """Compute Coriolis + centrifugal torques (qdd=0, g=0)."""
        return (self.inverse_dynamics(q, qd, np.zeros(self.n)) -
                self.gravity_torque(q))
