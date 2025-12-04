# app.py
# Streamlit Web Dashboard for Road Accident Simulation

import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

from constants import accident_types, LABO_BARANGAYS
from utils import sample_from_data_sources, build_environment_state, suggest_interventions, prepare_accident_entities, instantiate_entities, rng_for_location
from models import DriverProfile
from simulation import simulate_collision
from reporting import print_simulation_steps, generate_report, generate_pdf_report, create_map_visualization
from analysis import run_monte_carlo_intervention_analysis

st.title("Auto-Report System Dashboard")
st.sidebar.header("Simulation Parameters")

# User inputs
random_speed = st.sidebar.checkbox("Randomize Speed")
if random_speed:
    speed = st.sidebar.slider("Vehicle Speed (km/h)", 0, 150, 60, disabled=True)
else:
    speed = st.sidebar.slider("Vehicle Speed (km/h)", 0, 150, 60)
weather_options = ["Sunny", "Rainy", "Foggy", "Cloudy"]
weather = st.sidebar.selectbox("Weather", ["Random"] + weather_options)
accident_type = st.sidebar.selectbox("Accident Type", ["Random"] + list(accident_types.keys()))
location = st.sidebar.selectbox("Location", ["Random", "Main Highway"] + list(LABO_BARANGAYS.keys()))
moving_vehicles = st.sidebar.checkbox("Animate moving vehicles on map", value=True)
vehicle_roads_limit = st.sidebar.slider("Max roads animated", 1, 100, 50)
vehicles_per_road = 1
fps = st.sidebar.slider("Map FPS", 1, 60, 30)

if st.button("Simulate Crash"):
    # Handle random location selection
    if location == "Random":
        import random
        possible_locations = ["Main Highway"] + list(LABO_BARANGAYS.keys())
        location = random.choice(possible_locations)
        st.info(f"Randomly selected location: {location}")

    if accident_type == "Random":
        import random
        accident_type = random.choice(list(accident_types.keys()))
        st.info(f"Randomly selected accident type: {accident_type}")

    if weather == "Random":
        import random
        weather = random.choice(weather_options)
        st.info(f"Randomly selected weather: {weather}")

    if random_speed:
        import random
        speed = random.randint(20, 120)
        st.info(f"Randomly selected speed: {speed} km/h")

    # Sample parameters based on inputs and location when available
    cause, sampled_location, primary_vehicle_type, road_condition, lighting_condition, weather_condition, human_factor = sample_from_data_sources(location=location, seed_from_location=True)
    primary_vehicle_type = "Car"
    road_condition = "dry" if weather == "Sunny" else "wet"
    lighting_condition = "good"
    human_factor = "None"

    environment = build_environment_state(location, road_condition, lighting_condition, weather)
    driver_profile = DriverProfile.from_factor(human_factor)
    intervention_plan = suggest_interventions(location, cause, environment.road_condition, environment.lighting_condition, human_factor)

    rng = rng_for_location(location)
    vehicle1_spec, vehicle2_spec, pedestrian_spec, angle_of_impact = prepare_accident_entities(accident_type, primary_vehicle_type, rng)
    # Override speed
    if vehicle1_spec:
        vehicle1_spec["velocity"] = speed / 3.6  # Convert km/h to m/s
    baseline_vehicle1, baseline_vehicle2, baseline_pedestrian = instantiate_entities(vehicle1_spec, vehicle2_spec, pedestrian_spec)

    # Run simulation
    pos1, pos2, vel1, vel2, sim_time, impact_force, severity, risk_score, sim_data, ml_prediction = simulate_collision(
        baseline_vehicle1,
        baseline_vehicle2,
        pedestrian=baseline_pedestrian,
        accident_type=accident_type,
        environment=environment,
        driver_profile=driver_profile,
        verbose=False,
        location=location
    )

    st.success(f"Crash Detected! Severity: {severity.capitalize()}, Impact Force: {impact_force:.0f} N")

    # Display results
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Simulation Results")
        st.write(f"Collision Time: {sim_time:.2f} s")
        st.write(f"Risk Score: {risk_score:.2f}")
        st.write(f"Environment: {environment.describe()}")

    with col2:
        st.subheader("Recommendations")
        if intervention_plan.interventions:
            for intervention in intervention_plan.interventions:
                st.write(f"- {intervention.replace('_', ' ').title()}")
        else:
            st.write("No specific interventions recommended.")

    # Plot
    fig, ax = plt.subplots()
    time_array = np.arange(0, len(pos1)) * 0.01
    ax.plot(time_array, pos1, label=baseline_vehicle1.name if baseline_vehicle1 else "Vehicle")
    if baseline_vehicle2:
        ax.plot(time_array, pos2, label=baseline_vehicle2.name)
    elif baseline_pedestrian:
        ax.plot(time_array, pos2, label=baseline_pedestrian.name)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Position (m)')
    ax.legend()
    ax.set_title('Entity Positions During Simulation')
    st.pyplot(fig)

    # Generate and display map visualization
    st.subheader("Accident Location Map")
    try:
        # Get coordinates for the location (using Labo coordinates from constants)
        # Resolve coordinate from constants; fallback to general Labo center
        accident_lat, accident_lon = LABO_BARANGAYS.get(location, (14.156, 122.83))

        # Warn user in UI about high-FPS large-map issues
        if fps >= 30 and moving_vehicles and vehicle_roads_limit > 20:
            st.warning("High FPS with many animated roads can create very large map HTML payloads and may slow down or crash some browsers. Try lowering FPS or reducing animated roads.")

        # Create map visualization
        map_html = create_map_visualization(
            accident_location=(accident_lat, accident_lon),
            accident_type=accident_type,
            severity=severity,
            entities=[baseline_vehicle1.name if baseline_vehicle1 else "Vehicle 1",
                     baseline_vehicle2.name if baseline_vehicle2 else "Vehicle 2",
                     baseline_pedestrian.name if baseline_pedestrian else "Pedestrian"],
            timestamp=datetime.now()
            ,animate_vehicles=moving_vehicles, vehicle_roads_limit=vehicle_roads_limit, vehicles_per_road=vehicles_per_road, target_fps=fps)

        # Display the map in Streamlit
        components.html(map_html, height=600)

    except Exception as e:
        st.error(f"Error generating map: {str(e)}")
        st.info("Map visualization requires internet connection for tile loading.")

    # Generate and display report
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
        vehicle1_spec.get("velocity") if vehicle1_spec else None,
        vehicle2_spec.get("velocity") if vehicle2_spec else None,
        cause,
        location,
        angle_of_impact=angle_of_impact,
        weather=environment.weather_condition,
        driver_profile=driver_profile,
        environment=environment,
        risk_score=risk_score,
        intervention_plan=intervention_plan,
        validation_text="",
        comparison=None,
        ml_prediction=ml_prediction
    )
    st.session_state['report_text'] = report
    
    # Store simulation parameters for later report regeneration
    st.session_state['last_simulation'] = {
        'vehicle1': baseline_vehicle1,
        'vehicle2': baseline_vehicle2,
        'pedestrian': baseline_pedestrian,
        'accident_type': accident_type,
        'collision_time': sim_time,
        'impact_force': impact_force,
        'severity': severity,
        'road_condition': environment.road_condition,
        'lighting': environment.lighting_condition,
        'initial_v1': vehicle1_spec.get("velocity") if vehicle1_spec else None,
        'initial_v2': vehicle2_spec.get("velocity") if vehicle2_spec else None,
        'cause': cause,
        'location': location,
        'angle_of_impact': angle_of_impact,
        'weather': environment.weather_condition,
        'driver_profile': driver_profile,
        'environment': environment,
        'risk_score': risk_score,
        'intervention_plan': intervention_plan,
        'validation_text': "",
        'ml_prediction': ml_prediction
    }

    st.subheader("Generated Report")
    st.text_area("Report", report, height=300)

if 'report_text' in st.session_state:
    # PDF Generation
    if st.button("Generate PDF Report"):
        pdf_file = generate_pdf_report(st.session_state['report_text'])
        if pdf_file:
            st.success(f"PDF report generated: {pdf_file}")
        else:
            st.error("Failed to generate PDF. Install reportlab: pip install reportlab")

st.markdown("---")
st.header("Intervention Scenario Comparison")
st.write("Run a Monte Carlo analysis to compare accident outcomes with and without recommended interventions.")

if st.button("Run Comparison Analysis"):
    with st.spinner("Running Monte Carlo simulations..."):
        comparison_results = run_monte_carlo_intervention_analysis(runs=20)
    
    if comparison_results:
        baseline = comparison_results['baseline']
        intervention = comparison_results['intervention']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Baseline (No Interventions)")
            st.metric("Avg Risk Score", baseline.get('average_risk_score', 'N/A'))
            st.metric("Avg Impact Force", f"{baseline.get('average_impact_force', 0):.0f} N")
            st.write("Severity Distribution:")
            st.write({k: v for k, v in baseline.items() if k not in ['average_risk_score', 'average_impact_force']})
            
        with col2:
            st.subheader("With Interventions")
            st.metric("Avg Risk Score", intervention.get('average_risk_score', 'N/A'), 
                     delta=round(intervention.get('average_risk_score', 0) - baseline.get('average_risk_score', 0), 2),
                     delta_color="inverse")
            st.metric("Avg Impact Force", f"{intervention.get('average_impact_force', 0):.0f} N",
                     delta=f"{intervention.get('average_impact_force', 0) - baseline.get('average_impact_force', 0):.0f} N",
                     delta_color="inverse")
            st.write("Severity Distribution:")
            st.write({k: v for k, v in intervention.items() if k not in ['average_risk_score', 'average_impact_force']})
            
        # Visualization of improvement
        st.subheader("Improvement Analysis")
        risk_reduction = ((baseline.get('average_risk_score', 0) - intervention.get('average_risk_score', 0)) / baseline.get('average_risk_score', 1)) * 100
        st.success(f"Interventions reduced average risk score by {risk_reduction:.1f}%")

        # Update report if a simulation has been run
        if 'last_simulation' in st.session_state:
            sim_params = st.session_state['last_simulation']
            updated_report = generate_report(
                vehicle1=sim_params['vehicle1'],
                vehicle2=sim_params['vehicle2'],
                pedestrian=sim_params['pedestrian'],
                accident_type=sim_params['accident_type'],
                collision_time=sim_params['collision_time'],
                impact_force=sim_params['impact_force'],
                severity=sim_params['severity'],
                road_condition=sim_params['road_condition'],
                lighting=sim_params['lighting'],
                initial_v1=sim_params['initial_v1'],
                initial_v2=sim_params['initial_v2'],
                cause=sim_params['cause'],
                location=sim_params['location'],
                angle_of_impact=sim_params['angle_of_impact'],
                weather=sim_params['weather'],
                driver_profile=sim_params['driver_profile'],
                environment=sim_params['environment'],
                risk_score=sim_params['risk_score'],
                intervention_plan=sim_params['intervention_plan'],
                validation_text=sim_params['validation_text'],
                comparison=comparison_results,
                ml_prediction=sim_params['ml_prediction']
            )
            st.session_state['report_text'] = updated_report
            st.info("Report updated with intervention comparison results.")
            st.text_area("Updated Report", updated_report, height=300)