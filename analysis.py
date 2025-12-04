# analysis.py
# Analysis functions for Monte Carlo simulations and statistical analysis

import random
from typing import Dict, Optional

import pandas as pd

from constants import accident_types
from utils import sample_from_data_sources, build_environment_state, suggest_interventions, instantiate_entities, prepare_accident_entities, rng_for_location
from models import DriverProfile
from simulation import simulate_collision


def run_monte_carlo_simulations(runs: int = 50, apply_interventions: bool = False) -> Dict:
    """Execute multiple simulations to observe severity distribution trends."""

    results = []
    for _ in range(runs):
        cause, location, primary_vehicle_type, road_condition, lighting_condition, weather_condition, human_factor = sample_from_data_sources(force_uniform_location=True)
        environment = build_environment_state(location, road_condition, lighting_condition, weather_condition)
        driver_profile = DriverProfile.from_factor(human_factor)
        intervention_plan = suggest_interventions(location, cause, environment.road_condition, environment.lighting_condition, human_factor)
        accident_type = random.choice(list(accident_types.keys()))
        rng = rng_for_location(location)
        vehicle1_spec, vehicle2_spec, pedestrian_spec, angle = prepare_accident_entities(accident_type, primary_vehicle_type, rng)
        vehicle1, vehicle2, pedestrian = instantiate_entities(vehicle1_spec, vehicle2_spec, pedestrian_spec)

        _, _, _, _, _, impact_force, severity, risk_score, _, _ = simulate_collision(
            vehicle1,
            vehicle2,
            pedestrian=pedestrian,
            accident_type=accident_type,
            road_condition=environment.road_condition,
            lighting_condition=environment.lighting_condition,
            angle_of_impact=angle,
            environment=environment,
            driver_profile=driver_profile,
            interventions=intervention_plan.interventions if apply_interventions and intervention_plan.interventions else None,
            location=location,
            verbose=False
        )

        results.append({
            "severity": severity,
            "risk_score": risk_score,
            "location": location,
            "impact_force": impact_force
        })

    if not results:
        return {}

    df = pd.DataFrame(results)
    distribution = df['severity'].value_counts().to_dict()
    distribution['average_risk_score'] = float(round(df['risk_score'].mean(), 2)) if not df['risk_score'].isna().all() else None
    distribution['average_impact_force'] = float(round(df['impact_force'].mean(), 2))
    return distribution


def run_monte_carlo_intervention_analysis(runs: int = 20) -> Dict:
    """Compare baseline vs intervention outcomes using identical random scenarios."""

    baseline_records = []
    intervention_records = []

    for _ in range(runs):
        cause, location, primary_vehicle_type, road_condition, lighting_condition, weather_condition, human_factor = sample_from_data_sources(force_uniform_location=True)
        environment = build_environment_state(location, road_condition, lighting_condition, weather_condition)
        driver_profile = DriverProfile.from_factor(human_factor)
        intervention_plan = suggest_interventions(location, cause, environment.road_condition, environment.lighting_condition, human_factor)
        accident_type = random.choice(list(accident_types.keys()))
        rng = rng_for_location(location)
        vehicle1_spec, vehicle2_spec, pedestrian_spec, angle = prepare_accident_entities(accident_type, primary_vehicle_type, rng)

        # Baseline run
        vehicle1_base, vehicle2_base, pedestrian_base = instantiate_entities(vehicle1_spec, vehicle2_spec, pedestrian_spec)
        _, _, _, _, _, force_base, severity_base, risk_base, _, _ = simulate_collision(
            vehicle1_base,
            vehicle2_base,
            pedestrian=pedestrian_base,
            accident_type=accident_type,
            road_condition=environment.road_condition,
            lighting_condition=environment.lighting_condition,
            angle_of_impact=angle,
            environment=environment,
            driver_profile=driver_profile,
            interventions=None,
            location=location,
            verbose=False
        )
        baseline_records.append({
            "severity": severity_base,
            "risk_score": risk_base,
            "impact_force": force_base
        })

        # Intervention run (if plan active)
        vehicle1_int, vehicle2_int, pedestrian_int = instantiate_entities(vehicle1_spec, vehicle2_spec, pedestrian_spec)
        _, _, _, _, _, force_int, severity_int, risk_int, _, _ = simulate_collision(
            vehicle1_int,
            vehicle2_int,
            pedestrian=pedestrian_int,
            accident_type=accident_type,
            road_condition=environment.road_condition,
            lighting_condition=environment.lighting_condition,
            angle_of_impact=angle,
            environment=environment,
            driver_profile=driver_profile,
            interventions=intervention_plan.interventions if intervention_plan.interventions else None,
            location=location,
            verbose=False
        )
        intervention_records.append({
            "severity": severity_int,
            "risk_score": risk_int,
            "impact_force": force_int
        })

    def summarize(records):
        df = pd.DataFrame(records)
        distribution = df['severity'].value_counts().to_dict()
        distribution['average_risk_score'] = float(round(df['risk_score'].mean(), 2)) if not df['risk_score'].isna().all() else None
        distribution['average_impact_force'] = float(round(df['impact_force'].mean(), 2))
        return distribution

    if not baseline_records:
        return {}

    return {
        'baseline': summarize(baseline_records),
        'intervention': summarize(intervention_records)
    }