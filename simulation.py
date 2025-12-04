# simulation.py
# Core simulation functions for road accident modeling

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List, Any

from constants import intervention_effects
from models import EnvironmentState, DriverProfile, Vehicle, Pedestrian


def simulate_collision(
    vehicle1: Optional[Vehicle],
    vehicle2: Optional[Vehicle] = None,
    pedestrian: Optional[Pedestrian] = None,
    accident_type: str = "rear-end",
    dt: float = 0.01,
    total_time: float = 10.0,
    road_condition: str = "dry",
    lighting_condition: str = "good",
    angle_of_impact: int = 0,
    environment: Optional[EnvironmentState] = None,
    driver_profile: Optional[DriverProfile] = None,
    interventions: Optional[List[str]] = None,
    verbose: bool = True,
    location: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float, str, Optional[float], pd.DataFrame, str]:
    """
    Simulate the motion of two vehicles until collision or time out.
    Assume vehicle1 is behind vehicle2 for rear-end collision.
    angle_of_impact: 0 for rear-end, 180 for head-on, etc. (in degrees)
    location: name of the location (e.g., barangay or Main Highway) for reporting and ML prediction. If None,
              ML prediction falls back to 'Main Highway'.
    """
    # Set friction and reaction using environment-aware modeling
    if environment:
        friction_coeff = environment.get_effective_friction(driver_profile)
        reaction_time = environment.get_effective_reaction(driver_profile)
    else:
        friction_map = {"dry": 0.8, "wet": 0.5, "slippery": 0.1}
        friction_coeff = friction_map.get(road_condition, 0.8)
        reaction_map = {"good": 0.5, "poor": 1.5}
        reaction_time = reaction_map.get(lighting_condition, 0.5)

    # Apply interventions effects before simulation starts
    if interventions:
        for intervention in interventions:
            effects = intervention_effects.get(intervention)
            if not effects:
                continue
            if 'lighting_override' in effects and environment:
                environment = EnvironmentState(
                    road_condition=environment.road_condition,
                    lighting_condition=effects['lighting_override'],
                    weather_condition=environment.weather_condition,
                    slope=environment.slope,
                    curvature=environment.curvature
                )
                reaction_time = environment.get_effective_reaction(driver_profile)
            if 'road_condition_override' in effects and environment:
                environment = EnvironmentState(
                    road_condition=effects['road_condition_override'],
                    lighting_condition=environment.lighting_condition,
                    weather_condition=environment.weather_condition,
                    slope=environment.slope,
                    curvature=environment.curvature
                )
                friction_coeff = environment.get_effective_friction(driver_profile)
            if 'friction_bonus' in effects:
                friction_coeff = min(1.2, friction_coeff + effects['friction_bonus'])
            if 'reaction_multiplier' in effects:
                reaction_time *= effects['reaction_multiplier']
            if 'driver_risk_multiplier' in effects and driver_profile:
                driver_profile = DriverProfile(
                    factor=driver_profile.factor,
                    reaction_multiplier=driver_profile.reaction_multiplier,
                    braking_multiplier=driver_profile.braking_multiplier,
                    risk_multiplier=driver_profile.risk_multiplier * effects['driver_risk_multiplier'],
                    notes=driver_profile.notes
                )
            if 'speed_reduction' in effects:
                reduction = max(0.0, min(0.6, effects['speed_reduction']))
                if vehicle1:
                    vehicle1.velocity *= (1 - reduction)
                if vehicle2:
                    vehicle2.velocity *= (1 - reduction * 0.5)

    reaction_time = max(0.2, min(reaction_time, 3.5))
    friction_coeff = max(0.05, min(friction_coeff, 1.2))

    # Apply braking only for rear-end collisions
    if accident_type == "rear-end" and vehicle1:
        vehicle1.apply_braking(friction_coeff, reaction_time)
    
    # Set up entities based on accident type
    entities = [vehicle1] if vehicle1 else []
    if vehicle2:
        entities.append(vehicle2)
    if pedestrian:
        entities.append(pedestrian)
    
    # Initialize positions and velocities lists
    positions = {entity.name: [entity.position.copy()] for entity in entities}
    velocities = {entity.name: [entity.velocity.copy()] for entity in entities}
    
    time = 0
    collision_distance = 5  # meters
    impact_force = 0
    severity = "none"
    
    while time < total_time:
        # Update all entities
        for entity in entities:
            if hasattr(entity, 'update_position'):
                entity.update_position(dt)
            # Pedestrian doesn't move
        
        # Record positions and velocities
        for entity in entities:
            positions[entity.name].append(entity.position.copy())
            velocities[entity.name].append(entity.velocity.copy())
        
        # Check for collision based on type
        collided = False
        if accident_type == "rear-end" and vehicle2:
            if vehicle1.position[0] >= vehicle2.position[0] - collision_distance and vehicle1.velocity[0] > vehicle2.velocity[0]:
                collided = True
        elif accident_type == "head-on" and vehicle2:
            if abs(vehicle1.position[0] - vehicle2.position[0]) < collision_distance and vehicle1.velocity[0] > 0 and vehicle2.velocity[0] < 0:
                collided = True
        elif accident_type == "side-impact" and vehicle2:
            if vehicle1.position[0] >= vehicle2.position[0] - collision_distance:
                collided = True
        elif accident_type == "pedestrian" and pedestrian:
            if vehicle1.position[0] >= pedestrian.position[0] - collision_distance:
                collided = True
        
        if collided:
            if verbose:
                # vehicle positions are numpy arrays [x, y]; report x-coordinate for clarity
                pos_x = float(vehicle1.position[0]) if hasattr(vehicle1, 'position') and len(vehicle1.position) > 0 else float(vehicle1.position)
                print(f"Collision detected at time {time:.2f}s, position {pos_x:.2f} m")
            # Calculate impact force
            if accident_type == "pedestrian":
                v1_initial = velocities[vehicle1.name][-1][0]  # current velocity x-component before collision
                total_mass = vehicle1.mass + pedestrian.mass
                v_final = (vehicle1.mass * v1_initial + pedestrian.mass * pedestrian.velocity[0]) / total_mass
                delta_v = abs(v1_initial - v_final)
                impact_force = vehicle1.mass * delta_v / dt
                vehicle1.velocity[0] = v_final
                pedestrian.velocity[0] = v_final
            else:
                # Vehicle-vehicle collision
                v1_before = velocities[vehicle1.name][-2][0] if len(velocities[vehicle1.name]) > 1 else velocities[vehicle1.name][-1][0]
                total_mass = vehicle1.mass + vehicle2.mass
                v_final = (vehicle1.mass * vehicle1.velocity[0] + vehicle2.mass * vehicle2.velocity[0]) / total_mass
                vehicle1.velocity[0] = v_final
                vehicle2.velocity[0] = v_final
                delta_v = abs(vehicle1.velocity[0] - v1_before)
                impact_force = vehicle1.mass * delta_v / dt
            
            # Adjust impact force based on environmental modifiers and angle of impact
            slope_factor = 1.0
            curvature_factor = 1.0
            if environment:
                slope_factor += abs(environment.slope) / 50.0
                if environment.curvature in {"blind_curve", "sharp_turn"}:
                    curvature_factor += 0.2
            angle_factor = 1 + abs(np.sin(np.deg2rad(angle_of_impact))) * 0.3
            impact_force *= slope_factor * curvature_factor * angle_factor

            # Classify severity
            if impact_force < 50000:
                severity = "minor"
            elif impact_force < 150000:
                severity = "moderate"
            else:
                severity = "severe"
            if verbose:
                print(f"Impact force: {impact_force:.2f} N, Severity: {severity}")
            break
        
        time += dt
    
    # Create DataFrame
    max_len = max(len(pos) for pos in positions.values())
    time_array = np.arange(0, max_len) * dt
    sim_data = pd.DataFrame({'time': time_array})
    for name in positions:
        pos_array = np.array(positions[name])
        vel_array = np.array(velocities[name])
        sim_data[f'position_x_{name.lower().replace(" ", "_")}'] = pos_array[:, 0] if pos_array.ndim > 1 else pos_array
        sim_data[f'position_y_{name.lower().replace(" ", "_")}'] = pos_array[:, 1] if pos_array.ndim > 1 else np.zeros_like(pos_array)
        sim_data[f'velocity_x_{name.lower().replace(" ", "_")}'] = vel_array[:, 0] if vel_array.ndim > 1 else vel_array
        sim_data[f'velocity_y_{name.lower().replace(" ", "_")}'] = vel_array[:, 1] if vel_array.ndim > 1 else np.zeros_like(vel_array)
        # Pad with last values
        for col in [f'position_x_{name.lower().replace(" ", "_")}', f'position_y_{name.lower().replace(" ", "_")}', 
                    f'velocity_x_{name.lower().replace(" ", "_")}', f'velocity_y_{name.lower().replace(" ", "_")}']:
            if len(sim_data[col]) < max_len:
                last_val = sim_data[col].iloc[-1]
                sim_data[col] = sim_data[col].append(pd.Series([last_val] * (max_len - len(sim_data[col]))))
    
    # For compatibility, set pos1, pos2, vel1, vel2 to x-components
    pos1 = np.array([p[0] for p in positions.get(vehicle1.name if vehicle1 else "", [])])
    vel1 = np.array([v[0] for v in velocities.get(vehicle1.name if vehicle1 else "", [])])
    if vehicle2:
        pos2 = np.array([p[0] for p in positions.get(vehicle2.name, [])])
        vel2 = np.array([v[0] for v in velocities.get(vehicle2.name, [])])
    elif pedestrian:
        pos2 = np.array([p[0] for p in positions.get(pedestrian.name, [])])
        vel2 = np.array([v[0] for v in velocities.get(pedestrian.name, [])])
    else:
        pos2 = np.array([])
        vel2 = np.array([])
    
    from utils import calculate_risk_score
    risk_score = calculate_risk_score(impact_force, severity, environment, driver_profile)

    # Add location metadata to sim_data when available and ensure simulation returns it
    try:
        from constants import LABO_BARANGAYS
        if 'location' not in sim_data.columns:
            sim_data['location'] = None
        if 'latitude' not in sim_data.columns:
            sim_data['latitude'] = None
        if 'longitude' not in sim_data.columns:
            sim_data['longitude'] = None
    except Exception:
        LABO_BARANGAYS = {}

    # Populate columns if a location was passed
    if location:
        sim_data['location'] = location
        coords = LABO_BARANGAYS.get(location)
        if coords:
            sim_data['latitude'] = coords[0]
            sim_data['longitude'] = coords[1]

    # ML Severity Prediction
    ml_prediction = "ML Prediction disabled"

    return np.array(pos1), np.array(pos2), np.array(vel1), np.array(vel2), time, impact_force, severity, risk_score, sim_data, ml_prediction