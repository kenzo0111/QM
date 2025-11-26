# main.py
# Main entry point for road accident simulation

import random
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

from constants import accident_types
from utils import sample_from_data_sources, build_environment_state, suggest_interventions, prepare_accident_entities, instantiate_entities
from models import DriverProfile
from simulation import simulate_collision
from reporting import print_simulation_steps, generate_report
from analysis import run_monte_carlo_intervention_analysis


# Example simulation
if __name__ == "__main__":
    # Randomize accident type
    accident_type = random.choice(list(accident_types.keys()))
    print(f"Simulating accident type: {accident_type}")
    
    # Sample parameters from historical data sources (PDF Materials and Methods A. Data Sources)
    cause, location, primary_vehicle_type, road_condition, lighting_condition, weather_condition, human_factor = sample_from_data_sources()
    print(f"Based on data sources: Location={location}, Cause={cause}, Road={road_condition}, Lighting={lighting_condition}, Weather={weather_condition}, Human Factor={human_factor}")

    environment = build_environment_state(location, road_condition, lighting_condition, weather_condition)
    driver_profile = DriverProfile.from_factor(human_factor)
    intervention_plan = suggest_interventions(location, cause, environment.road_condition, environment.lighting_condition, human_factor)

    vehicle1_spec, vehicle2_spec, pedestrian_spec, angle_of_impact = prepare_accident_entities(accident_type, primary_vehicle_type)
    baseline_vehicle1, baseline_vehicle2, baseline_pedestrian = instantiate_entities(vehicle1_spec, vehicle2_spec, pedestrian_spec)

    initial_v1 = vehicle1_spec["velocity"] if vehicle1_spec else None
    initial_v2 = vehicle2_spec["velocity"] if vehicle2_spec else None

    print_simulation_steps(
        accident_type,
        cause,
        location,
        environment.road_condition,
        environment.lighting_condition,
        baseline_vehicle1,
        baseline_vehicle2,
        baseline_pedestrian,
        weather=environment.weather_condition,
        driver_profile=driver_profile,
        environment=environment,
        interventions=intervention_plan
    )

    # Baseline simulation without interventions
    pos1, pos2, vel1, vel2, sim_time, impact_force, severity, risk_score, sim_data, ml_prediction = simulate_collision(
        baseline_vehicle1,
        baseline_vehicle2,
        pedestrian=baseline_pedestrian,
        accident_type=accident_type,
        road_condition=environment.road_condition,
        lighting_condition=environment.lighting_condition,
        angle_of_impact=angle_of_impact,
        environment=environment,
        driver_profile=driver_profile,
        interventions=None,
        verbose=True
    )

    print("Simulation Data (baseline):")
    print(sim_data.head())

    # Intervention simulation for what-if comparison
    if intervention_plan.interventions:
        intervention_vehicle1, intervention_vehicle2, intervention_pedestrian = instantiate_entities(vehicle1_spec, vehicle2_spec, pedestrian_spec)
        _, _, _, _, sim_time_int, impact_force_int, severity_int, risk_score_int, _, _ = simulate_collision(
            intervention_vehicle1,
            intervention_vehicle2,
            pedestrian=intervention_pedestrian,
            accident_type=accident_type,
            road_condition=environment.road_condition,
            lighting_condition=environment.lighting_condition,
            angle_of_impact=angle_of_impact,
            environment=environment,
            driver_profile=driver_profile,
            interventions=intervention_plan.interventions,
            verbose=False
        )
    else:
        severity_int = severity
        impact_force_int = impact_force
        risk_score_int = risk_score
        sim_time_int = sim_time

    comparison_payload = {
        "baseline": {
            "severity": severity,
            "impact_force": impact_force,
            "risk_score": risk_score,
            "collision_time": sim_time
        },
        "intervention": {
            "severity": severity_int,
            "impact_force": impact_force_int,
            "risk_score": risk_score_int,
            "collision_time": sim_time_int
        }
    } if intervention_plan.interventions else None

    from utils import validate_with_historical
    validation_text = validate_with_historical(location, severity)

    report = generate_report(
        baseline_vehicle1,
        baseline_vehicle2,
        baseline_pedestrian,
        accident_type,
        sim_time,
        impact_force,
        severity,
        environment.road_condition,
        environment.lighting_condition,
        initial_v1,
        initial_v2,
        cause,
        location,
        angle_of_impact=angle_of_impact,
        weather=environment.weather_condition,
        driver_profile=driver_profile,
        environment=environment,
        risk_score=risk_score,
        intervention_plan=intervention_plan,
        validation_text=validation_text,
        comparison=comparison_payload,
        ml_prediction=ml_prediction
    )
    print(report)

    # Monte Carlo analysis offers a quick predictive snapshot for planning
    monte_carlo_summary = run_monte_carlo_intervention_analysis(runs=20)
    if monte_carlo_summary:
        print(f"Monte Carlo comparison (baseline vs interventions): {monte_carlo_summary}")

    from reporting import create_labo_roads_geojson, create_map_visualization
    geojson_path = create_labo_roads_geojson()
    if geojson_path is None:
        print("Warning: Could not prepare GIS/labo_roads.geojson. The map overlay may be missing.")
    else:
        print(f"Prepared road overlay at {geojson_path}")

    create_map_visualization(
        sim_data,
        vehicle1_name=baseline_vehicle1.name if baseline_vehicle1 else "Vehicle 1",
        vehicle2_name=baseline_vehicle2.name if baseline_vehicle2 else None,
        pedestrian_name=baseline_pedestrian.name if baseline_pedestrian else None,
        location=location,
        labo_geojson_path=geojson_path,
        collision_time=sim_time
    )

    # Persist results for longitudinal analysis (append rather than overwrite)
    if severity != "none":
        try:
            new_accident = {
                'cause': cause,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'location': location,
                'vehicle_type': primary_vehicle_type,
                'weather': environment.weather_condition,
                'lighting': 'Daylight' if environment.lighting_condition == 'good' else 'Night',
                'road_characteristics': {
                    'dry': 'Dry road',
                    'wet': 'Wet road',
                    'slippery': 'Slippery surface'
                }.get(environment.road_condition, environment.road_condition),
                'human_factors': human_factor,
                'severity': severity.capitalize()
            }

            try:
                import pandas as pd
                historical_df = pd.read_csv('accident_data.csv')
                historical_df = pd.concat([historical_df, pd.DataFrame([new_accident])], ignore_index=True)
            except FileNotFoundError:
                historical_df = pd.DataFrame([new_accident])

            historical_df.to_csv('accident_data.csv', index=False)
            print(f"Accident data appended to accident_data.csv: {severity.capitalize()} accident in {location}")
        except Exception as e:
            print(f"Could not save accident data to CSV: {e}")
    else:
        print("No collision occurred - accident not saved to database")

    # Plot positions
    time_array = np.arange(0, len(pos1)) * 0.01
    plt.plot(time_array, pos1, label=baseline_vehicle1.name if baseline_vehicle1 else "Vehicle")
    if baseline_vehicle2:
        plt.plot(time_array, pos2, label=baseline_vehicle2.name)
    elif baseline_pedestrian:
        plt.plot(time_array, pos2, label=baseline_pedestrian.name)
    plt.xlabel('Time (s)')
    plt.ylabel('Position (m)')
    plt.legend()
    plt.title('Entity Positions During Simulation')
    # plt.show()  # Commented out to avoid blocking