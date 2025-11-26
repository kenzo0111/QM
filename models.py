# models.py
# Data models and classes for road accident simulation

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class TelemetryData:
    timestamp: float
    g_force_x: float
    g_force_y: float
    velocity: float

class CrashDetector:
    def __init__(self, g_force_threshold=2.5):
        self.threshold = g_force_threshold

    def analyze_stream(self, telemetry_stream: list[TelemetryData]) -> bool:
        """Simulates an automatic trigger based on sensor readings."""
        for data in telemetry_stream:
            # Automatic detection logic
            if abs(data.g_force_x) > self.threshold or abs(data.g_force_y) > self.threshold:
                return True
        return False

from constants import human_factor_profiles


@dataclass
class DriverProfile:
    """Represents the human factor component affecting reaction and braking."""

    factor: str = "None"
    reaction_multiplier: float = 1.0
    braking_multiplier: float = 1.0
    risk_multiplier: float = 1.0
    notes: str = ""

    @classmethod
    def from_factor(cls, factor: str) -> "DriverProfile":
        normalized = (factor or "None").strip()
        profile_key = None
        for key in human_factor_profiles:
            if normalized.lower() == key.lower():
                profile_key = key
                break
        if profile_key is None:
            profile_key = "None"
        profile_data = human_factor_profiles.get(profile_key, human_factor_profiles["None"])
        return cls(
            factor=profile_key,
            reaction_multiplier=profile_data["reaction_multiplier"],
            braking_multiplier=profile_data["braking_multiplier"],
            risk_multiplier=profile_data["risk_multiplier"],
            notes=profile_data["notes"]
        )


@dataclass
class EnvironmentState:
    """Encodes the road, lighting, and weather conditions for the simulation."""

    road_condition: str
    lighting_condition: str
    weather_condition: str
    slope: float = 0.0  # degrees incline/decline approximation
    curvature: str = "straight"  # straight, intersection, blind_curve, etc.

    def get_effective_friction(self, driver_profile: Optional[DriverProfile] = None) -> float:
        base_friction = {"dry": 0.82, "wet": 0.55, "slippery": 0.18}.get(self.road_condition, 0.75)
        # Wetter weather decreases traction further
        if self.weather_condition.lower() in {"rainy", "storm", "typhoon"}:
            base_friction *= 0.9
        # Uphill/Downhill adjustments based on Systems Theory interaction of vehicle-road
        base_friction *= max(0.7, 1 - abs(self.slope) * 0.01)
        if self.curvature in {"blind_curve", "sharp_turn"}:
            base_friction *= 0.95
        if driver_profile:
            base_friction *= driver_profile.braking_multiplier
        for max_limit in (1.2,):
            base_friction = min(base_friction, max_limit)
        return max(base_friction, 0.05)

    def get_effective_reaction(self, driver_profile: Optional[DriverProfile] = None) -> float:
        base_reaction = {"good": 0.55, "poor": 1.5}.get(self.lighting_condition, 0.8)
        if self.weather_condition.lower() in {"rainy", "foggy", "storm"}:
            base_reaction *= 1.2
        if driver_profile:
            base_reaction *= driver_profile.reaction_multiplier
        return max(0.3, min(base_reaction, 3.5))

    def describe(self) -> str:
        return (
            f"Road: {self.road_condition}, Lighting: {self.lighting_condition}, Weather: {self.weather_condition}, "
            f"Slope: {self.slope:.1f}°, Geometry: {self.curvature}"
        )


@dataclass
class InterventionPlan:
    """Represents selected interventions for what-if analysis."""

    interventions: list[str] = field(default_factory=list)

    def describe(self) -> str:
        if not self.interventions:
            return "No interventions applied."
        return ", ".join(
            f"{name.replace('_', ' ').title()}" for name in self.interventions
        )


class Vehicle:
    def __init__(self, mass: float, initial_velocity: float, position: np.ndarray = None, name: str = "Vehicle"):
        self.mass = mass  # kg
        self.velocity = np.array([initial_velocity, 0.0]) if isinstance(initial_velocity, (int, float)) else initial_velocity  # m/s [vx, vy]
        if position is not None:
            if isinstance(position, (int, float)):
                self.position = np.array([float(position), 0.0])  # m [x, y]
            else:
                self.position = np.array(position, dtype=float)
        else:
            self.position = np.array([0.0, 0.0])  # m [x, y]
        self.name = name
        self.acceleration = np.array([0.0, 0.0])  # m/s^2 [ax, ay]
        self.braking = False
        self.reaction_time = 0  # seconds
        self.braking_timer = 0
        self.engine_force = 0  # N (simplified, can be set externally)

    def update_position(self, dt: float):
        if self.braking and self.braking_timer <= 0:
            # Calculate braking deceleration with friction
            speed = np.linalg.norm(self.velocity)
            if speed > 0:
                drag_direction = -self.velocity / speed
                self.acceleration = drag_direction * self.friction_coeff * 9.81
            else:
                self.acceleration = np.array([0.0, 0.0])
        else:
            # Simplified physics: engine force vs drag
            speed = np.linalg.norm(self.velocity)
            if speed > 0:
                drag = 0.5 * 1.2 * 2.2 * speed**2  # Air resistance approximation
                drag_force = drag * (-self.velocity / speed)
                net_force = self.engine_force * (self.velocity / speed) + drag_force
                self.acceleration = net_force / self.mass
            else:
                self.acceleration = np.array([0.0, 0.0])

        self.position += self.velocity * dt + 0.5 * self.acceleration * dt**2
        self.velocity += self.acceleration * dt

        # Only stop at zero when braking (not for initial negative velocities in head-on collisions)
        if self.braking and np.linalg.norm(self.velocity) < 0.1:
            self.velocity = np.array([0.0, 0.0])  # stop at zero only when braking
        if self.braking_timer > 0:
            self.braking_timer -= dt

    def apply_braking(self, friction_coeff: float, reaction_time: float = 0):
        self.friction_coeff = friction_coeff
        self.reaction_time = reaction_time
        self.braking_timer = reaction_time
        self.braking = True


class Pedestrian:
    def __init__(self, mass: float = 70, position: np.ndarray = None, name: str = "Pedestrian"):
        self.mass = mass  # kg
        if position is not None:
            if isinstance(position, (int, float)):
                self.position = np.array([float(position), 0.0])  # m [x, y]
            else:
                self.position = np.array(position, dtype=float)
        else:
            self.position = np.array([0.0, 0.0])  # m [x, y]
        self.name = name
        self.velocity = np.array([0.0, 0.0])  # pedestrians don't move in this simple model

    def update_position(self, dt: float):
        # Pedestrians don't move
        pass