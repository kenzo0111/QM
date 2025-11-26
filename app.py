# app.py
# Streamlit Web Dashboard for Road Accident Simulation

import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

from constants import accident_types
from utils import sample_from_data_sources, build_environment_state, suggest_interventions, prepare_accident_entities, instantiate_entities
from models import DriverProfile
from simulation import simulate_collision
from reporting import print_simulation_steps, generate_report, generate_pdf_report, create_map_visualization
from analysis import run_monte_carlo_intervention_analysis

st.title("Auto-Report System Dashboard")
st.sidebar.header("Simulation Parameters")

# User inputs
speed = st.sidebar.slider("Vehicle Speed (km/h)", 0, 150, 60)
weather_options = ["Sunny", "Rainy", "Foggy", "Cloudy"]
weather = st.sidebar.selectbox("Weather", weather_options)
accident_type = st.sidebar.selectbox("Accident Type", list(accident_types.keys()))
location = st.sidebar.selectbox("Location", ["Bayabas", "Main Highway", "Barangay 1", "Barangay 2", "Barangay 3", "Barangay 4", "Barangay 5"])
moving_vehicles = st.sidebar.checkbox("Animate moving vehicles on map", value=True)
vehicle_roads_limit = st.sidebar.slider("Max roads animated", 1, 100, 50)
vehicles_per_road = st.sidebar.slider("Vehicles per animated road", 1, 3, 1)

if st.button("Simulate Crash"):
    # Sample parameters based on inputs
    cause = "Overspeeding"  # Simplified
    primary_vehicle_type = "Car"
    road_condition = "dry" if weather == "Sunny" else "wet"
    lighting_condition = "good"
    human_factor = "None"

    environment = build_environment_state(location, road_condition, lighting_condition, weather)
    driver_profile = DriverProfile.from_factor(human_factor)
    intervention_plan = suggest_interventions(location, cause, environment.road_condition, environment.lighting_condition, human_factor)

    vehicle1_spec, vehicle2_spec, pedestrian_spec, angle_of_impact = prepare_accident_entities(accident_type, primary_vehicle_type)
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
        verbose=False
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
        from constants import LABO_COORDINATES
        accident_lat, accident_lon = LABO_COORDINATES.get(location, (14.1568, 121.3997))  # Default to Labo center

        # Create map visualization
        map_html = create_map_visualization(
            accident_location=(accident_lat, accident_lon),
            accident_type=accident_type,
            severity=severity,
            entities=[baseline_vehicle1.name if baseline_vehicle1 else "Vehicle 1",
                     baseline_vehicle2.name if baseline_vehicle2 else "Vehicle 2",
                     baseline_pedestrian.name if baseline_pedestrian else "Pedestrian"],
            timestamp=datetime.now()
            ,animate_vehicles=moving_vehicles, vehicle_roads_limit=vehicle_roads_limit, vehicles_per_road=vehicles_per_road)

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
    st.subheader("Generated Report")
    st.text_area("Report", report, height=300)

    # PDF Generation
    if st.button("Generate PDF Report"):
        pdf_file = generate_pdf_report(report)
        if pdf_file:
            st.success(f"PDF report generated: {pdf_file}")
        else:
            st.error("Failed to generate PDF. Install reportlab: pip install reportlab")