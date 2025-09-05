import math
import random
import time
from dataclasses import dataclass
from typing import Tuple, Dict

MAT_W = 300.0
MAT_H = 300.0

@dataclass
class Pose:
    x: float
    y: float
    theta: float
    ts: float = 0.0

@dataclass
class Params:
    v_roam: float = 15.0
    v_tired_rot_deg: float = 7.5
    v_stressed: float = 35.0
    v_lazy: float = 15.0
    safety_radius: float = 40.0
    boundary_margin: float = 25.0
    max_turn_rate: float = math.radians(90)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

class RoamingController:
    def __init__(self, params: Params):
        self.p = params

    def step(self, pose: Pose, dt: float, repel_vec=(0.0, 0.0)):
        vx = math.cos(pose.theta)
        vy = math.sin(pose.theta)

        rx, ry = 0.0, 0.0
        if pose.x < self.p.boundary_margin: rx += (self.p.boundary_margin - pose.x)
        if pose.x > MAT_W - self.p.boundary_margin: rx -= (pose.x - (MAT_W - self.p.boundary_margin))
        if pose.y < self.p.boundary_margin: ry += (self.p.boundary_margin - pose.y)
        if pose.y > MAT_H - self.p.boundary_margin: ry -= (pose.y - (MAT_H - self.p.boundary_margin))

        rx += repel_vec[0]; ry += repel_vec[1]

        desired_theta = math.atan2(vy + 0.005*ry, vx + 0.005*rx)
        dtheta = (desired_theta - pose.theta + math.pi) % (2*math.pi) - math.pi
        dtheta = clamp(dtheta, -self.p.max_turn_rate*dt, self.p.max_turn_rate*dt)

        return velocity_to_wheels(self.p.v_roam, 0.0, dtheta, dt)

class TiredController:
    def __init__(self, params: Params): self.p = params
    def step(self, pose: Pose, dt: float, **_):
        omega = math.radians(self.p.v_tired_rot_deg)
        return velocity_to_wheels(0.0, omega, 0.0, dt)

class StressedController:
    def __init__(self, params: Params):
        self.p = params
        self._segment_t = 0.0
        self._segment_dur = 1.2

    def step(self, pose: Pose, dt: float, repel_vec=(0.0, 0.0)):
        self._segment_t += dt
        if self._segment_t >= self._segment_dur:
            self._segment_t = 0.0
            delta = 0.0
            if near_edge(pose, self.p.boundary_margin * 1.5):
                delta = random.choice([math.pi/2, -math.pi/2, math.pi])
            else:
                delta = random.choice([0.0, math.pi/2, -math.pi/2])
            pose.theta = (pose.theta + delta) % (2*math.pi)
        return velocity_to_wheels(self.p.v_stressed, 0.0, 0.0, dt)

class LazyController:
    def __init__(self, params: Params):
        self.p = params
        self._target = None

    def step(self, pose: Pose, dt: float, **_):
        if self._target is None:
            corners = [(0,0), (MAT_W,0), (0,MAT_H), (MAT_W,MAT_H)]
            self._target = min(corners, key=lambda c: (pose.x-c[0])**2+(pose.y-c[1])**2)
        tx, ty = self._target
        dx, dy = tx - pose.x, ty - pose.y
        dist = math.hypot(dx, dy)
        if dist < 10.0:
            return (0.0, 0.0)
        heading = math.atan2(dy, dx)
        return velocity_to_wheels(self.p.v_lazy, 0.0, (heading - pose.theta), dt)

def near_edge(pose: Pose, margin: float) -> bool:
    return (pose.x < margin or pose.x > MAT_W - margin or pose.y < margin or pose.y > MAT_H - margin)

WHEEL_BASE = 40.0

def velocity_to_wheels(v_forward: float, omega: float, heading_delta: float, dt: float):
    kp = 2.0
    omega_cmd = omega + kp * (heading_delta / max(dt, 1e-3))
    v_l = v_forward - (omega_cmd * WHEEL_BASE / 2.0)
    v_r = v_forward + (omega_cmd * WHEEL_BASE / 2.0)
    return (v_l, v_r)

class CubeStateMachine:
    def __init__(self, cube_id: str, state: str, params: Params | None = None):
        self.cube_id = cube_id
        self.state = state
        self.p = params or Params()
        self.last_pose = Pose(150.0, 150.0, 0.0, time.time())
        self._controllers = {
            "roaming": RoamingController(self.p),
            "tired": TiredController(self.p),
            "stressed": StressedController(self.p),
            "lazy": LazyController(self.p),
        }

    def update_pose(self, x: float, y: float, theta_deg: float):
        self.last_pose = Pose(x, y, math.radians(theta_deg), time.time())

    def step(self, dt: float, repel_vec=(0.0,0.0)):
        ctrl = self._controllers[self.state]
        if self.state in ("roaming", "stressed"):
            return ctrl.step(self.last_pose, dt, repel_vec=repel_vec)
        else:
            return ctrl.step(self.last_pose, dt)

def compute_repulsions(poses: Dict[str, Pose], safety_radius: float):
    out = {cid:(0.0,0.0) for cid in poses}
    for a_id, a in poses.items():
        rx, ry = 0.0, 0.0
        for b_id, b in poses.items():
            if a_id == b_id: continue
            dx, dy = a.x - b.x, a.y - b.y
            d = math.hypot(dx, dy)
            if d < 1e-6: continue
            if d < safety_radius:
                strength = (safety_radius - d) / safety_radius
                rx += (dx / d) * strength * 10.0
                ry += (dy / d) * strength * 10.0
        out[a_id] = (rx, ry)
    return out
