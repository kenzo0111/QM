# utils.py
# Utility functions for road accident simulation

import random
import pandas as pd
from typing import Optional, Tuple, Dict, Any
import zlib

from constants import location_profiles, vehicle_types, accident_types, barangay_names
from models import EnvironmentState, InterventionPlan, DriverProfile


def build_environment_state(location: str, road_condition: str, lighting_condition: str, weather_condition: str) -> EnvironmentState:
    """Create an EnvironmentState incorporating field observations per location."""

    profile = location_profiles.get(location, {})
    slope = profile.get("slope", 0.0)
    curvature = profile.get("curvature", "straight")
    # If weather not provided, fallback to location default gleaned from field observations
    weather = weather_condition or profile.get("default_weather", "Sunny")
    return EnvironmentState(
        road_condition=road_condition,
        lighting_condition=lighting_condition,
        weather_condition=weather,
        slope=slope,
        curvature=curvature
    )


def suggest_interventions(location: str, cause: str, road_condition: str, lighting_condition: str, human_factor: str) -> InterventionPlan:
    """Suggest interventions grounded in Materials & Methods and Systems Theory."""

    plan = InterventionPlan()
    profile = location_profiles.get(location, {})
    plan.interventions.extend(profile.get("recommended_interventions", []))

    if lighting_condition == "poor" and "improved_street_lighting" not in plan.interventions:
        plan.interventions.append("improved_street_lighting")
    if road_condition in {"wet", "slippery"} and "road_surface_treatment" not in plan.interventions:
        plan.interventions.append("road_surface_treatment")
    if cause == "Overspeeding" and "speed_checkpoint" not in plan.interventions:
        plan.interventions.append("speed_checkpoint")
    if human_factor.lower() in {"under influence", "drunk driving"} and "speed_checkpoint" not in plan.interventions:
        plan.interventions.append("speed_checkpoint")
    if human_factor.lower() in {"fatigue", "sleepy driver"} and "driver_safety_campaign" not in plan.interventions:
        plan.interventions.append("driver_safety_campaign")

    # Ensure uniqueness while preserving order
    seen = set()
    deduped = []
    for intervention in plan.interventions:
        if intervention not in seen:
            deduped.append(intervention)
            seen.add(intervention)
    plan.interventions = deduped
    return plan


def calculate_risk_score(impact_force: float, severity: str, environment: Optional[EnvironmentState], driver_profile: Optional[DriverProfile]) -> float:
    """Compute a 0-10 risk score blending vehicle, road, and human factors."""

    severity_weights = {"none": 0.0, "minor": 4.0, "moderate": 7.0, "severe": 9.0}
    base_score = severity_weights.get(severity.lower(), 5.0)
    base_score += min(impact_force / 150000, 2.5)

    if environment:
        if environment.road_condition != "dry":
            base_score += 0.7
        if environment.lighting_condition == "poor":
            base_score += 0.6
        base_score += min(abs(environment.slope) / 10.0, 1.0)
        if environment.curvature in {"blind_curve", "intersection"}:
            base_score += 0.5

    if driver_profile:
        base_score *= driver_profile.risk_multiplier

    return round(max(0.0, min(10.0, base_score)), 2)


def generate_systemic_summary(cause: str, driver_profile: Optional[DriverProfile], environment: Optional[EnvironmentState], plan: Optional[InterventionPlan], vehicle1: Optional[Any] = None, vehicle2: Optional[Any] = None, pedestrian: Optional[Any] = None, initial_v1: Optional[float] = None, initial_v2: Optional[float] = None) -> str:
    """Create a systems theory summary based on the accident cause."""

    cause_summaries = {
        "Overspeeding": "Overspeeding amplifies the impact of poor road conditions and reduces reaction time, leading to severe collisions in systems theory where human factors interact with vehicle dynamics and environmental constraints.",
        "Drunk Driving": "Drunk driving impairs human judgment and reaction time, interacting with vehicle control systems and road geometry to create hazardous situations in systems theory.",
        "Mechanical Failure": "Mechanical failure in vehicle systems interacts with human response capabilities and road conditions, creating unexpected hazards in systems theory.",
        "Fatigue": "Driver fatigue reduces reaction time and decision-making, interacting with lighting conditions and road geometry in systems theory to increase accident risk.",
        "Poor Visibility": "Poor visibility limits human perception, interacting with vehicle lighting and road markings in systems theory to compromise safety margins.",
        "Reckless Driving": "Reckless driving combines aggressive human behavior with vehicle capabilities and environmental factors in systems theory, leading to high-risk interactions.",
        "Human Error": "Human error in judgment or action interacts with vehicle systems and environmental conditions in systems theory, creating accident scenarios.",
        "Mechanical Failure": "Mechanical failure in vehicle systems interacts with human response capabilities and road conditions, creating unexpected hazards in systems theory."
    }

    return cause_summaries.get(cause, f"{cause} contributes to accidents through complex interactions in systems theory involving human, vehicle, and environmental factors.")


def validate_with_historical(location: str, severity: str) -> str:
    """Compare simulated severity against historical distribution for validation."""

    try:
        historical = pd.read_csv('accident_data.csv')
    except Exception:
        return "Historical validation unavailable (no data)."

    if historical.empty or 'severity' not in historical.columns:
        return "Historical validation unavailable (insufficient data)."

    location_data = historical[historical['location'] == location]
    if location_data.empty:
        return f"No recorded accidents in {location} for validation."

    severity_counts = location_data['severity'].astype(str).str.lower().value_counts()
    total = severity_counts.sum()
    match_count = severity_counts.get(severity.lower(), 0)
    percentage = (match_count / total) * 100 if total else 0
    return f"{percentage:.1f}% of historical accidents in {location} share {severity.lower()} severity."


def determine_angle(accident_type: str) -> int:
    angle_map = {"rear-end": 0, "head-on": 180, "side-impact": 90, "pedestrian": 15}
    return angle_map.get(accident_type, 0)


def prepare_accident_entities(accident_type: str, primary_vehicle_type: str, rng: Optional[random.Random] = None) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict], int]:
    """Create baseline entity specifications for repeatable simulation/what-if runs."""

    def vehicle_spec(position: float, name_suffix: str, velocity: Optional[float] = None) -> Dict:
        r = rng or random
        veh_type = primary_vehicle_type
        mass = r.randint(*vehicle_types[veh_type]["mass_range"])
        speed = velocity if velocity is not None else r.uniform(15, 35)
        return {"mass": mass, "velocity": speed, "position": position, "name": f"{veh_type} {name_suffix}"}

    vehicle1 = vehicle_spec(0, "1")
    vehicle2 = None
    pedestrian = None

    if accident_type == "rear-end":
        vehicle2 = vehicle_spec(50, "2")
        if vehicle1["velocity"] <= vehicle2["velocity"]:
            vehicle1["velocity"] = vehicle2["velocity"] + (rng or random).uniform(5, 10)
    elif accident_type == "head-on":
        vehicle1["velocity"] = (rng or random).uniform(15, 25)
        vehicle2 = vehicle_spec(100, "2", velocity=-(rng or random).uniform(15, 25))
    elif accident_type == "side-impact":
        vehicle1["velocity"] = (rng or random).uniform(15, 25)
        vehicle2 = vehicle_spec(50, "2", velocity=0)
    elif accident_type == "pedestrian":
        vehicle1["velocity"] = random.uniform(15, 35)
        pedestrian = {"mass": (rng or random).randint(50, 90), "position": (rng or random).uniform(40, 60), "name": "Pedestrian"}

    angle = determine_angle(accident_type)
    return vehicle1, vehicle2, pedestrian, angle


def rng_for_location(location: Optional[str]) -> random.Random:
    """Return a deterministic Random seeded by a stable hash of the location name.

    This enables consistent randomness tied to a barangay name while keeping the
    global random state untouched.
    """
    seed = 0
    if location:
        try:
            seed = zlib.crc32(str(location).encode('utf-8'))
        except Exception:
            seed = abs(hash(location)) % (2**32)
    return random.Random(seed)


def instantiate_entities(vehicle1_spec: Optional[Dict], vehicle2_spec: Optional[Dict], pedestrian_spec: Optional[Dict]) -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
    from models import Vehicle, Pedestrian
    vehicle1 = Vehicle(vehicle1_spec["mass"], vehicle1_spec["velocity"], position=vehicle1_spec["position"], name=vehicle1_spec["name"]) if vehicle1_spec else None
    vehicle2 = Vehicle(vehicle2_spec["mass"], vehicle2_spec["velocity"], position=vehicle2_spec["position"], name=vehicle2_spec["name"]) if vehicle2_spec else None
    pedestrian = Pedestrian(mass=pedestrian_spec["mass"], position=pedestrian_spec["position"], name=pedestrian_spec["name"]) if pedestrian_spec else None
    return vehicle1, vehicle2, pedestrian


def generate_recommendations(cause: str, road_condition: str, lighting_condition: str, accident_type: str) -> list[str]:
    """Generate randomized recommendations based on accident factors"""
    from constants import recommendations_db
    recs = []
    
    # Add cause-specific recommendations
    if cause in recommendations_db:
        recs.extend(random.sample(recommendations_db[cause], min(2, len(recommendations_db[cause]))))
    
    # Add road condition recommendations
    if road_condition in recommendations_db:
        recs.extend(random.sample(recommendations_db[road_condition], min(1, len(recommendations_db[road_condition]))))
    
    # Add lighting recommendations
    if lighting_condition in recommendations_db:
        recs.extend(random.sample(recommendations_db[lighting_condition], min(1, len(recommendations_db[lighting_condition]))))
    
    # Add accident type recommendations
    if accident_type in recommendations_db:
        recs.extend(random.sample(recommendations_db[accident_type], min(1, len(recommendations_db[accident_type]))))
    
    # Remove duplicates and limit to 4-5 recommendations
    recs = list(set(recs))[:5]
    
    return recs


def sample_from_data_sources(location: Optional[str] = None, seed_from_location: bool = False, force_uniform_location: bool = False) -> Tuple[str, str, str, str, str, str, str]:
    """Sample accident parameters from historical data sources"""
    try:
        accident_data = pd.read_csv('accident_data.csv')
    except Exception:
        # Fallback to default if file not found
        accident_data = pd.DataFrame([
            ['Overspeeding', '2023-01-15 14:30', 'Bayabas', 'Car', 'Sunny', 'Daylight', 'Dry road', 'Fatigue', 'Moderate'],
            ['Human Error', '2023-02-20 22:00', 'Main Highway', 'Motorcycle', 'Rainy', 'Night', 'Slippery surface', 'Drunk Driving', 'Severe'],
            ['Mechanical Failure', '2023-03-10 08:15', 'Barangay 1', 'Truck', 'Cloudy', 'Daylight', 'Blind curve', 'None', 'Minor'],
            ['Fatigue', '2023-04-05 23:45', 'Bayabas', 'Car', 'Clear', 'Night', 'Dark area', 'Sleepy driver', 'Moderate'],
            ['Drunk Driving', '2023-05-12 01:20', 'Main Highway', 'Car', 'Rainy', 'Night', 'Wet road', 'Under influence', 'Severe']
        ], columns=['cause', 'time', 'location', 'vehicle_type', 'weather', 'lighting', 'road_characteristics', 'human_factors', 'severity'])

    # Optionally filter data by location
    if location is not None and 'location' in accident_data.columns:
        filtered = accident_data[accident_data['location'].astype(str).str.lower() == str(location).lower()]
        if not filtered.empty:
            if seed_from_location:
                seed = zlib.crc32(str(location).encode('utf-8'))
                row = filtered.sample(random_state=seed).iloc[0]
            else:
                row = filtered.sample().iloc[0]
        else:
            # fallback to sampling from all data
            row = accident_data.sample().iloc[0]
    else:
        row = accident_data.sample().iloc[0]

    # Map data to simulation parameters
    cause = row.get('cause', 'Overspeeding')
    if force_uniform_location and location is None:
        # Uniformly sample location across known profiles when requested. This helps avoid
        # strongly biased historical datasets (e.g., too many 'Main Highway' entries).
        try:
            location_choices = barangay_names
            import random as _random
            location = _random.choice(location_choices)
        except Exception:
            location = row.get('location', 'Bayabas')
    else:
        location = row.get('location', 'Bayabas')

    # Map vehicle type
    vehicle_type_map = {
        'Car': 'Car',
        'Motorcycle': 'Motorcycle',
        'Truck': 'Truck',
        'Bus': 'Bus'
    }
    vehicle_type = vehicle_type_map.get(row.get('vehicle_type', 'Car'), 'Car')

    # Map road condition
    road_char = str(row.get('road_characteristics', 'Dry road')).lower()
    if 'slippery' in road_char:
        road_condition = 'slippery'
    elif 'wet' in road_char:
        road_condition = 'wet'
    else:
        road_condition = 'dry'

    # Map lighting condition
    lighting_map = {
        'Night': 'poor',
        'Dusk': 'poor',
        'Daylight': 'good'
    }
    lighting_condition = lighting_map.get(row.get('lighting', 'Daylight'), 'good')

    # Weather information
    weather_raw = str(row.get('weather', 'Sunny'))
    weather_condition = weather_raw.title()
    if 'rainy' in weather_raw.lower() and road_condition == 'dry':
        road_condition = 'wet'

    human_factor = str(row.get('human_factors', 'None'))

    return cause, location, vehicle_type, road_condition, lighting_condition, weather_condition, human_factor