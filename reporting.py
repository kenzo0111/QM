# reporting.py
# Reporting and visualization functions for road accident simulation

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Dict, Any, List
import os
import json
import random
from pathlib import Path
from datetime import datetime

# GIS and mapping libraries
try:
    import geopandas as gpd
    from shapely.geometry import LineString, MultiLineString
    import osmnx as ox
    import folium
    from branca.element import MacroElement
    from jinja2 import Template
    import pandas as pd
except ImportError as e:
    print(f"Warning: Some GIS/mapping libraries not available: {e}")

from constants import accident_types
from utils import generate_recommendations, generate_systemic_summary, validate_with_historical
from models import EnvironmentState, DriverProfile, InterventionPlan


def print_simulation_steps(accident_type: str, cause: str, location: str, road_condition: str, lighting_condition: str, vehicle1: Optional[Any], vehicle2: Optional[Any], pedestrian: Optional[Any], weather: Optional[str], driver_profile: Optional[DriverProfile], environment: Optional[EnvironmentState], interventions: Optional[InterventionPlan]):
    """Print step-by-step breakdown of the road accident simulation process"""
    print("\n" + "="*80)
    print("ROAD ACCIDENT SIMULATION STEPS")
    print("="*80)
    
    print(f"\nStep 1: Accident Scenario Setup")
    print(f"   - Accident Type: {accident_types[accident_type]['description']}")
    print(f"   - Location: {location}, Labo, Camarines Norte")
    print(f"   - Primary Cause: {cause}")
    print(f"   - Road Conditions: {road_condition}")
    print(f"   - Lighting Conditions: {lighting_condition}")
    if weather:
        print(f"   - Weather: {weather}")
    if environment:
        print(f"   - Road Geometry: {environment.curvature}, Approx. Slope: {environment.slope:.1f}°")
    if driver_profile:
        print(f"   - Driver State: {driver_profile.factor} ({driver_profile.notes})")
    
    print(f"\nStep 2: Vehicle/Pedestrian Initialization")
    if vehicle1:
        speed_kmh = np.linalg.norm(vehicle1.velocity) * 3.6
        print(f"   - Vehicle 1: {vehicle1.name} (Mass: {vehicle1.mass} kg, Initial Speed: {speed_kmh:.1f} km/h)")
    if vehicle2:
        speed_kmh = np.linalg.norm(vehicle2.velocity) * 3.6
        print(f"   - Vehicle 2: {vehicle2.name} (Mass: {vehicle2.mass} kg, Initial Speed: {speed_kmh:.1f} km/h)")
    if pedestrian:
        print(f"   - Pedestrian: {pedestrian.name} (Mass: {pedestrian.mass} kg, Position: {pedestrian.position:.1f} m)")
    
    print(f"\nStep 3: Environmental Factors Applied")
    friction_map = {"dry": 0.8, "wet": 0.5, "slippery": 0.1}
    reaction_map = {"good": 0.5, "poor": 1.5}
    friction_coeff = friction_map.get(road_condition, 0.8)
    reaction_time = reaction_map.get(lighting_condition, 0.5)
    if environment:
        friction_coeff = environment.get_effective_friction(driver_profile)
        reaction_time = environment.get_effective_reaction(driver_profile)
    print(f"   - Friction Coefficient: {friction_coeff} (based on {road_condition} road)")
    print(f"   - Driver Reaction Time: {reaction_time}s (based on {lighting_condition} lighting)")
    
    if accident_type == "rear-end":
        print(f"   - Braking Applied: Vehicle 1 applies brakes after {reaction_time}s reaction time")
    
    print(f"\nStep 4: Physics Simulation Begins")
    print(f"   - Time Step: 0.01 seconds")
    print(f"   - Total Simulation Time: 10.0 seconds")
    print(f"   - Collision Detection Distance: 5.0 meters")
    
    print(f"\nStep 5: Motion Calculation")
    print(f"   - Position updates using kinematic equations:")
    print(f"     position = position + velocity * time + 0.5 * acceleration * time^2")
    print(f"     velocity = velocity + acceleration * time")
    
    if accident_type == "rear-end":
        deceleration = friction_coeff * 9.81
        print(f"   - Braking Deceleration: {deceleration:.1f} m/s² (friction * gravity)")
    
    print(f"\nStep 6: Collision Detection")
    if accident_type == "rear-end":
        print(f"   - Checking if Vehicle 1 overtakes Vehicle 2 within collision distance")
    elif accident_type == "head-on":
        print(f"   - Checking if vehicles meet within collision distance")
    elif accident_type == "side-impact":
        print(f"   - Checking perpendicular collision proximity")
    elif accident_type == "pedestrian":
        print(f"   - Checking if vehicle reaches pedestrian position")
    
    print(f"\nStep 7: Impact Analysis (if collision occurs)")
    print(f"   - Momentum Conservation: m1*v1 + m2*v2 = (m1+m2)*v_final")
    print(f"   - Impact Force Calculation: F = m * delta_v / delta_t")
    print(f"   - Severity Classification:")
    print(f"     • Minor: Impact Force < 50,000 N")
    print(f"     • Moderate: 50,000 N <= Impact Force < 150,000 N")
    print(f"     • Severe: Impact Force >= 150,000 N")
    
    print(f"\nStep 8: Data Recording")
    print(f"   - Position and velocity data collected every 0.01 seconds")
    print(f"   - Simulation data stored in pandas DataFrame")
    
    print(f"\nStep 9: Report Generation")
    print(f"   - Accident analysis and recommendations generated")
    print(f"   - Excel report created with formatted data")
    
    print(f"\nStep 10: Visualization")
    print(f"   - Position vs time plots generated for analysis")
    if interventions and interventions.interventions:
        print(f"\nStep 11: Intervention Modeling")
        from constants import intervention_effects
        for item in interventions.interventions:
            desc = intervention_effects.get(item, {}).get('description', 'Applied based on field recommendations')
            print(f"   - {item.replace('_', ' ').title()}: {desc}")
    
    print("\n" + "="*80)
    print("SIMULATION EXECUTION BEGINS")
    print("="*80 + "\n")


def generate_report(
    vehicle1: Optional[Any],
    vehicle2: Optional[Any],
    pedestrian: Optional[Any],
    accident_type: str,
    collision_time: float,
    impact_force: float,
    severity: str,
    road_condition: str,
    lighting: str,
    initial_v1: Optional[float],
    initial_v2: Optional[float],
    cause: str,
    location: str,
    angle_of_impact: int = 0,
    weather: Optional[str] = None,
    driver_profile: Optional[DriverProfile] = None,
    environment: Optional[EnvironmentState] = None,
    risk_score: Optional[float] = None,
    intervention_plan: Optional[InterventionPlan] = None,
    validation_text: Optional[str] = None,
    comparison: Optional[Dict] = None,
    ml_prediction: Optional[str] = None
) -> str:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.cell.cell import MergedCell

    accident_desc = accident_types[accident_type]["description"]
    geometry_summary = (
        f"Road Geometry: {environment.curvature} (Slope: {environment.slope:.1f}°)" if environment else "Road Geometry: Not specified"
    )
    report = f"""
Road Accident Simulation Report
================================

Accident Type: {accident_desc}
Location: {location}, Labo, Camarines Norte
Time of Accident: {collision_time:.2f} seconds into simulation
Cause: {cause}
Weather: {weather or 'Not recorded'}
{geometry_summary}

Vehicles Involved:
"""
    if vehicle1:
        report += f"- {vehicle1.name}: Mass = {vehicle1.mass} kg, Initial Speed = {initial_v1 * 3.6:.1f} km/h\n"
    if vehicle2:
        report += f"- {vehicle2.name}: Mass = {vehicle2.mass} kg, Initial Speed = {initial_v2 * 3.6:.1f} km/h\n"
    if pedestrian:
        report += f"- {pedestrian.name}: Mass = {pedestrian.mass} kg\n"
    
    recommendations = generate_recommendations(cause, road_condition, lighting, accident_type)
    recommendations_text = "\n".join(f"- {rec}" for rec in recommendations)
    system_summary = generate_systemic_summary(cause, driver_profile, environment, intervention_plan, vehicle1, vehicle2, pedestrian, initial_v1, initial_v2)
    validation_line = validation_text or "Historical validation unavailable."

    baseline_severity = comparison['baseline']['severity'] if comparison else severity
    intervention_severity = comparison['intervention']['severity'] if comparison else severity
    baseline_force = comparison['baseline']['impact_force'] if comparison else impact_force
    intervention_force = comparison['intervention']['impact_force'] if comparison else impact_force
    baseline_risk = comparison['baseline'].get('risk_score') if comparison else risk_score
    intervention_risk = comparison['intervention'].get('risk_score') if comparison else risk_score
    impact_force_reduction = None
    if comparison and baseline_force:
        impact_force_reduction = (baseline_force - intervention_force) / baseline_force * 100
    risk_reduction = None
    if comparison and baseline_risk:
        risk_reduction = baseline_risk - intervention_risk
    baseline_risk_formatted = f"{baseline_risk:.2f}" if baseline_risk is not None else "N/A"
    intervention_risk_formatted = f"{intervention_risk:.2f}" if intervention_risk is not None else "N/A"
    risk_change_text = (
        f"{risk_reduction:.2f} (Baseline {baseline_risk_formatted}, Intervention {intervention_risk_formatted})"
        if risk_reduction is not None and baseline_risk is not None and intervention_risk is not None
        else f"0.00 (Baseline {baseline_risk_formatted}, Intervention {intervention_risk_formatted})"
    )
    force_reduction_text = f"{impact_force_reduction:.2f}%" if impact_force_reduction is not None else "0%"
    intervention_desc = intervention_plan.describe() if intervention_plan else 'None'
    baseline_risk_text = baseline_risk_formatted
    intervention_risk_text = intervention_risk_formatted
    
    report += f"""

Analysis:
This simulation demonstrates how speed, road conditions, and lighting contribute to accidents.
Severity is classified based on impact force: minor (<50kN), moderate (50-150kN), severe (>150kN).
Recommendations:
{recommendations_text}

Systems Interaction Summary:
- {system_summary}

Validation Against Historical Records:
- {validation_line}

Intervention Scenario Comparison:
- Baseline Severity: {baseline_severity}
- Intervention Severity: {intervention_severity}
- Baseline Impact Force: {baseline_force:.2f} N
- Intervention Impact Force: {intervention_force:.2f} N
- Risk Score Change: {risk_change_text}
- Impact Force Reduction: {force_reduction_text}
- Interventions Applied: {intervention_desc}

Machine Learning Prediction:
{ml_prediction if ml_prediction else "Not available"}

"""
    # Create formatted Excel report
    wb = Workbook()
    ws = wb.active
    ws.title = "Accident Report"
    
    # Add title
    ws['A1'] = "Road Accident Simulation Report"
    ws['A1'].font = Font(size=16, bold=True)
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.merge_cells('A1:O1')
    
    # Add headers starting from row 3
    data = {
        'Accident Type': accident_desc,
        'Location': f"{location}, Labo, Camarines Norte",
        'Time of Accident': f"{collision_time:.2f} seconds",
        'Cause': cause,
        'Vehicle 1 Name': vehicle1.name if vehicle1 else '',
        'Vehicle 1 Mass (kg)': vehicle1.mass if vehicle1 else '',
        'Vehicle 1 Initial Speed (km/h)': f"{initial_v1 * 3.6:.1f}" if initial_v1 else '',
        'Vehicle 2 Name': vehicle2.name if vehicle2 else '',
        'Vehicle 2 Mass (kg)': vehicle2.mass if vehicle2 else '',
        'Vehicle 2 Initial Speed (km/h)': f"{initial_v2 * 3.6:.1f}" if initial_v2 else '',
        'Pedestrian Name': pedestrian.name if pedestrian else '',
        'Pedestrian Mass (kg)': pedestrian.mass if pedestrian else '',
        'Road Conditions': road_condition,
        'Lighting Conditions': lighting,
        'Weather': weather or 'Not recorded',
        'Angle of Impact (degrees)': angle_of_impact,
        'Collision Time (s)': f"{collision_time:.2f}",
        'Impact Force (N)': f"{impact_force:.2f}",
        'Severity': severity,
        'Risk Score (0-10)': risk_score if risk_score is not None else baseline_risk,
        'Analysis': 'This simulation demonstrates how speed, road conditions, and lighting contribute to accidents.',
        'Recommendations': recommendations_text,
        'Systems Summary': system_summary,
        'Historical Validation': validation_line,
        'Interventions Applied': intervention_desc,
        'Baseline Severity': baseline_severity,
        'Intervention Severity': intervention_severity,
        'Baseline Impact Force (N)': f"{baseline_force:.2f}",
        'Intervention Impact Force (N)': f"{intervention_force:.2f}",
        'Impact Force Reduction (%)': force_reduction_text,
        'Risk Score Change': risk_change_text,
        'Baseline Risk Score': baseline_risk_text,
        'Intervention Risk Score': intervention_risk_text
    }
    
    headers = list(data.keys())
    for col, header in enumerate(headers, 1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")  # Gold color
        ws.cell(row=3, column=col).alignment = Alignment(horizontal='center')
    
    # Add data
    for col, value in enumerate(data.values(), 1):
        ws.cell(row=4, column=col, value=value)
        ws.cell(row=4, column=col).alignment = Alignment(horizontal='center')
    
    # Auto-adjust column widths
    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        max_length = 0
        for row in range(1, 5):  # Check rows 1 to 4
            cell = ws.cell(row=row, column=col_num)
            if cell.value and not isinstance(cell, MergedCell):
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = min(max_length + 2, 30)  # Cap at 30 for readability
        ws.column_dimensions[column_letter].width = adjusted_width
    
    try:
        wb.save('accident_report.xlsx')
        print("Formatted Excel report saved as 'accident_report.xlsx'")
    except PermissionError:
        print("Could not save Excel report due to permission error. Report printed above.")
    
    return report


def create_labo_roads_geojson(force_regenerate: bool = False) -> Path | None:
    """Ensure a clipped Labo road network GeoJSON exists and return its path."""

    base_dir = Path(__file__).resolve().parent if '__file__' in globals() else Path(os.getcwd())
    gis_dir = base_dir / "GIS"
    output_geojson_path = gis_dir / "labo_roads.geojson"

    if output_geojson_path.exists() and not force_regenerate:
        print(f"Found existing {output_geojson_path}. Reusing it for the map overlay.")
        return output_geojson_path

    gis_dir.mkdir(parents=True, exist_ok=True)

    def pick_source(candidates: list[Path]) -> Path | None:
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    road_source = pick_source([
        gis_dir / "highway.shp",
        gis_dir / "Labo_Roads.shp",
        gis_dir / "labo_roads.geojson.shp"
    ])

    boundary_source = pick_source([
        gis_dir / "Labo_Boundary.shp",
        gis_dir / "Labo_Boundary.geojson",
        gis_dir / "Labo_Boundary.shp.gpkg"
    ])

    if road_source is None:
        print("No road network file found in the GIS directory. Expected 'highway.shp' or a Labo-specific layer.")
        return None

    print(f"Reading road network from {road_source}...")
    try:
        roads = gpd.read_file(road_source)
    except Exception as exc:
        print(f"Error reading road network layer: {exc}")
        return None

    clip_required = boundary_source is not None and road_source.name.lower() not in {"labo_roads.geojson.shp", "labo_roads.shp"}

    if clip_required:
        print(f"Reading Labo boundary from {boundary_source}...")
        try:
            boundary = gpd.read_file(boundary_source)
        except Exception as exc:
            print(f"Error reading boundary layer: {exc}")
            return None

        print("Clipping roads to the Labo boundary...")
        try:
            roads = gpd.clip(roads, boundary)
        except Exception as exc:
            print(f"Error during clipping: {exc}")
            return None
    else:
        if boundary_source is None:
            print("Boundary layer not found; exporting the available road layer as-is.")
        else:
            print("Detected an existing Labo-only road layer; skipping additional clipping.")

    if roads.empty:
        print("No road geometries found to export. GeoJSON will not be created.")
        return None

    print(f"Saving Labo road network to {output_geojson_path}...")
    try:
        roads.to_file(output_geojson_path, driver="GeoJSON")
    except Exception as exc:
        print(f"Error saving GeoJSON: {exc}")
        return None

    print("Success! labo_roads.geojson is ready.")
    return output_geojson_path


def create_map_visualization(
    accident_location: tuple[float, float],
    accident_type: str,
    severity: str,
    entities: List[str],
    timestamp: datetime
) -> str:
    """
    Creates a map visualization showing the accident location and relevant information.
    Returns HTML content for embedding in Streamlit.
    """
    print("\nStarting map visualization process...")

    accident_lat, accident_lon = accident_location

    # Create a base map centered on the accident location
    m = folium.Map(location=[accident_lat, accident_lon], zoom_start=15)

    # Add accident location marker with animated pulse
    accident_marker_css = """
    <style>
    .accident-marker {
        position: relative;
        width: 34px;
        height: 34px;
    }
    .accident-marker-core {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 18px;
        height: 18px;
        transform: translate(-50%, -50%);
        background: #d9534f;
        border-radius: 50%;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(217, 83, 79, 0.7);
        animation: accident-core-pulse 1.6s infinite;
    }
    .accident-marker-core i {
        font-size: 12px;
    }
    .accident-marker-wave {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 34px;
        height: 34px;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        border: 2px solid rgba(217, 83, 79, 0.7);
        opacity: 0;
        animation: accident-wave 2.4s infinite;
    }
    .accident-marker-wave.wave-delay {
        animation-delay: 1.2s;
    }
    @keyframes accident-wave {
        0% {
            opacity: 0.7;
            transform: translate(-50%, -50%) scale(0.3);
        }
        60% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.6);
        }
        100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.6);
        }
    }
    @keyframes accident-core-pulse {
        0%, 100% {
            transform: translate(-50%, -50%) scale(1);
            box-shadow: 0 0 10px rgba(217, 83, 79, 0.7);
        }
        50% {
            transform: translate(-50%, -50%) scale(1.15);
            box-shadow: 0 0 18px rgba(217, 83, 79, 0.9);
        }
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(accident_marker_css))

    accident_marker_html = """
    <div class="accident-marker">
        <div class="accident-marker-wave"></div>
        <div class="accident-marker-wave wave-delay"></div>
        <div class="accident-marker-core"><i class="fa fa-exclamation"></i></div>
    </div>
    """

    # Create popup content for accident marker
    popup_content = f"""
    <b>Accident Details</b><br>
    Type: {accident_type.replace('_', ' ').title()}<br>
    Severity: {severity.capitalize()}<br>
    Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
    Entities: {', '.join(entities) if entities else 'None'}
    """

    folium.Marker(
        location=[accident_lat, accident_lon],
        popup=popup_content,
        icon=folium.DivIcon(html=accident_marker_html, icon_size=(34, 34), icon_anchor=(17, 17), class_name='')
    ).add_to(m)

    # Add Labo road network overlay if available
    labo_geojson_path = Path(__file__).resolve().parent / "GIS" / "labo_roads.geojson"
    if labo_geojson_path.exists():
        try:
            roads_gdf = gpd.read_file(labo_geojson_path)
            if not roads_gdf.empty:
                roads_geojson_data = json.loads(roads_gdf.to_json())

                def road_style(_):
                    return {"color": "#ff7f0e", "weight": 3, "opacity": 0.85}

                folium.GeoJson(
                    roads_geojson_data,
                    name="Labo Road Network",
                    style_function=road_style
                ).add_to(m)
                folium.LayerControl().add_to(m)
                print("Added Labo road network overlay")
        except Exception as e:
            print(f"Could not load Labo roads: {e}")

    # Add historical accident data markers
    try:
        historical_data = pd.read_csv('accident_data.csv')
        location_counts = historical_data.groupby('location').size().reset_index(name='accident_count')

        # Accurate coordinates for Labo locations
        location_coords = {
            'Bayabas': [14.158, 122.825],
            'Main Highway': [14.156, 122.83],
            'Barangay 1': [14.152, 122.835],
            'Barangay 2': [14.154, 122.828],
            'Barangay 3': [14.160, 122.832],
            'Barangay 4': [14.158, 122.838],
            'Barangay 5': [14.162, 122.826],
        }

        for _, row in location_counts.iterrows():
            loc_name = row['location']
            count = row['accident_count']

            if loc_name in location_coords:
                marker_lat, marker_lon = location_coords[loc_name]
            else:
                continue

            # Color based on accident count
            if count >= 5:
                color = 'red'
            elif count >= 3:
                color = 'orange'
            else:
                color = 'blue'

            folium.Marker(
                location=[marker_lat, marker_lon],
                popup=f"<b>{loc_name}</b><br>Historical Accidents: {count}",
                icon=folium.Icon(color=color, icon='exclamation-triangle', prefix='fa')
            ).add_to(m)

        print(f"Added {len(location_counts)} historical accident markers")
    except Exception as e:
        print(f"Could not load historical accident data: {e}")

    # Add moving traffic animation
    traffic_css = """
    <style>
    .traffic-flow {
        position: absolute;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, transparent 0%, rgba(0, 255, 0, 0.6) 20%, rgba(255, 255, 0, 0.8) 50%, rgba(255, 165, 0, 0.7) 80%, transparent 100%);
        animation: traffic-flow 8s linear infinite;
        pointer-events: none;
        z-index: 1000;
    }

    .traffic-vehicle {
        position: absolute;
        width: 8px;
        height: 8px;
        background: #ff4444;
        border-radius: 50%;
        animation: vehicle-move 12s linear infinite;
        box-shadow: 0 0 4px rgba(255, 68, 68, 0.8);
        z-index: 1001;
    }

    .traffic-vehicle:nth-child(2) {
        animation-delay: -4s;
        background: #4444ff;
        box-shadow: 0 0 4px rgba(68, 68, 255, 0.8);
    }

    .traffic-vehicle:nth-child(3) {
        animation-delay: -8s;
        background: #44ff44;
        box-shadow: 0 0 4px rgba(68, 255, 68, 0.8);
    }

    @keyframes traffic-flow {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    @keyframes vehicle-move {
        0% {
            transform: translateX(-20px) scale(0.8);
            opacity: 0;
        }
        10% {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
        90% {
            opacity: 1;
            transform: translateX(calc(100vw - 20px)) scale(1);
        }
        100% {
            transform: translateX(calc(100vw - 20px)) scale(0.8);
            opacity: 0;
        }
    }

    .traffic-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 999;
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(traffic_css))

    # Add simple traffic overlay without complex JavaScript
    traffic_overlay_html = """
    <div class="traffic-overlay">
        <!-- Traffic flow indicators on major roads -->
        <div class="traffic-flow" style="top: 45%; left: 0; transform: rotate(0deg);"></div>
        <div class="traffic-flow" style="top: 55%; left: 0; transform: rotate(0deg); animation-delay: -2s;"></div>
        <div class="traffic-flow" style="top: 25%; left: 0; transform: rotate(15deg); animation-delay: -1s;"></div>
        <div class="traffic-flow" style="top: 75%; left: 0; transform: rotate(-15deg); animation-delay: -3s;"></div>

        <!-- Moving vehicle markers -->
        <div class="traffic-vehicle" style="top: 48%; animation-duration: 10s;"></div>
        <div class="traffic-vehicle" style="top: 52%; animation-duration: 15s;"></div>
        <div class="traffic-vehicle" style="top: 28%; animation-duration: 12s;"></div>
        <div class="traffic-vehicle" style="top: 72%; animation-duration: 18s;"></div>
        <div class="traffic-vehicle" style="top: 35%; animation-duration: 14s;"></div>
    </div>
    """

    # Add traffic overlay to map
    m.get_root().html.add_child(folium.Element(traffic_overlay_html))

    print("Added moving traffic animation to map")

    # Add legend
    from branca.element import MacroElement
    from jinja2 import Template

    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999; background-color: white; border: 1px solid #ccc; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.25); padding: 12px 14px; font-size: 13px; line-height: 1.5; min-width: 250px;">
        <div style="font-weight: 600; margin-bottom: 8px;">Map Legend</div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display: inline-block; width: 26px; height: 4px; background-color: #ff7f0e; margin-right: 8px;"></span>
            <span>Labo road network</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <i class="fa fa-exclamation" style="color: #d9534f; margin-right: 8px;"></i>
            <span>Current accident location</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background: linear-gradient(90deg, #ff4444, #4444ff, #44ff44); margin-right: 8px; animation: pulse 2s infinite;"></div>
            <span>Moving traffic flow</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <i class="fa fa-exclamation-triangle" style="color: #d9534f; margin-right: 8px;"></i>
            <span>High accident density (≥5)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <i class="fa fa-exclamation-triangle" style="color: #f0ad4e; margin-right: 8px;"></i>
            <span>Moderate accident density (3-4)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <i class="fa fa-exclamation-triangle" style="color: #0275d8; margin-right: 8px;"></i>
            <span>Low accident density (&lt;3)</span>
        </div>
    </div>
    {% raw %}
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    </style>
    {% endraw %}
    {% endmacro %}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)

    # Add favicon to avoid 404 requests
    favicon_link = '<link rel="icon" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMBApZfo7kAAAAASUVORK5CYII=" />'
    m.get_root().header.add_child(folium.Element(favicon_link))

    # Return the HTML content instead of saving to file
    import tempfile
    import os

    # Create a temporary file to save the map
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_file:
        temp_filename = temp_file.name
        m.save(temp_filename)

    # Read the HTML content from the temporary file
    try:
        with open(temp_filename, 'r', encoding='utf-8') as f:
            html_string = f.read()
    finally:
        # Clean up the temporary file
        os.unlink(temp_filename)

    print("Map visualization generated successfully for Streamlit integration.")
    return html_string
def generate_pdf_report(report_text: str, filename: str = "accident_report.pdf"):
    """Generate a PDF report from the text report."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph("Road Accident Simulation Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Report content
        for line in report_text.split('\n'):
            if line.strip():
                p = Paragraph(line, styles['Normal'])
                story.append(p)
            else:
                story.append(Spacer(1, 6))

        doc.build(story)
        print(f"PDF report generated: {filename}")
        return filename
    except ImportError:
        print("reportlab not installed. Install with: pip install reportlab")
        return None