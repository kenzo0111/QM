# constants.py
# Global constants and data structures for road accident simulation

from __future__ import annotations

# Vehicle types with mass ranges (kg)
vehicle_types = {
    "Car": {"mass_range": (1200, 1500)},
    "Truck": {"mass_range": (5000, 10000)},
    "Motorcycle": {"mass_range": (150, 300)},
    "Bus": {"mass_range": (8000, 12000)}
}

# Accident types
accident_types = {
    "rear-end": {"description": "Rear-end collision"},
    "head-on": {"description": "Head-on collision"},
    "side-impact": {"description": "Side-impact (T-bone) collision"},
    "pedestrian": {"description": "Vehicle-pedestrian collision"}
}

# Possible causes
causes = ["Overspeeding", "Drunk Driving", "Mechanical Failure", "Fatigue", "Poor Visibility", "Reckless Driving"]

# Road and lighting conditions
road_conditions = ["dry", "wet", "slippery"]
lighting_conditions = ["good", "poor"]

# Possible recommendations based on accident factors
recommendations_db = {
    "Overspeeding": ["Implement speed cameras", "Increase speed limit enforcement", "Add speed bumps in high-risk areas"],
    "Drunk Driving": ["Stricter DUI checkpoints", "Public awareness campaigns on drinking and driving", "Install breathalyzer devices"],
    "Mechanical Failure": ["Mandatory vehicle inspections", "Improve maintenance education", "Create emergency roadside assistance programs"],
    "Fatigue": ["Install rest areas along highways", "Campaigns on driver fatigue awareness", "Regulate maximum driving hours"],
    "Poor Visibility": ["Upgrade street lighting", "Install reflective road signs", "Improve weather-responsive lighting systems"],
    "Reckless Driving": ["Enhanced driver training programs", "Increase traffic police presence", "Implement point-based license system"],
    "Human Error": ["Driver education and awareness programs", "Improve road signage", "Traffic signal optimization"],
    "dry": ["Regular road maintenance", "Pothole repair programs"],
    "wet": ["Improve drainage systems", "Install anti-skid road surfaces", "Weather-based speed limit adjustments"],
    "slippery": ["Apply anti-slip treatments", "Install warning signs for slippery areas", "Tire tread depth checks"],
    "good": ["Maintain current lighting standards"],
    "poor": ["Install additional street lights", "Upgrade to LED lighting systems", "Solar-powered lighting solutions"],
    "rear-end": ["Increase following distance education", "Install rear-end collision warning systems"],
    "head-on": ["Install median barriers", "Improve lane markings", "One-way traffic in narrow roads"],
    "side-impact": ["Improve intersection visibility", "Install turning signal cameras", "Enhanced crosswalk protections"],
    "pedestrian": ["Install pedestrian crossings", "Speed reduction near schools/zones", "Pedestrian safety education"]
}

# Human factor profiles influence driver reaction and braking effectiveness
human_factor_profiles = {
    "None": {"reaction_multiplier": 1.0, "braking_multiplier": 1.0, "risk_multiplier": 1.0, "notes": "Driver operating within normal alertness."},
    "None listed": {"reaction_multiplier": 1.0, "braking_multiplier": 1.0, "risk_multiplier": 1.0, "notes": "No reported impairment."},
    "Under influence": {"reaction_multiplier": 1.6, "braking_multiplier": 0.85, "risk_multiplier": 1.5, "notes": "Impaired decision making due to alcohol or substances."},
    "Drunk Driving": {"reaction_multiplier": 1.7, "braking_multiplier": 0.85, "risk_multiplier": 1.6, "notes": "Blood alcohol levels hamper perception and coordination."},
    "Fatigue": {"reaction_multiplier": 1.4, "braking_multiplier": 0.9, "risk_multiplier": 1.3, "notes": "Delayed reaction because of drowsiness."},
    "Sleepy driver": {"reaction_multiplier": 1.5, "braking_multiplier": 0.9, "risk_multiplier": 1.4, "notes": "Driver vigilance reduced due to lack of rest."},
    "None reported": {"reaction_multiplier": 1.0, "braking_multiplier": 1.0, "risk_multiplier": 1.0, "notes": "No recorded impairment."}
}

# Road location profiles capture geometry characteristics gathered from field observations
location_profiles = {
    "Bayabas": {
        "coords": [14.158, 122.825],  # Actual Lat/Lon for Bayabas, Labo
        "slope": 4.5, 
        "curvature": "blind_curve", 
        "default_weather": "Rainy", 
        "recommended_interventions": ["road_surface_treatment", "improved_street_lighting"]
    },
    "Main Highway": {
        "coords": [14.15, 122.83],  # Approximate Lat/Lon for Main Highway in Labo
        "slope": 1.0, 
        "curvature": "straight", 
        "default_weather": "Sunny", 
        "recommended_interventions": ["speed_checkpoint", "driver_safety_campaign"]
    },
    "Barangay 1": {
        "coords": [14.16, 122.82],  # Approximate Lat/Lon
        "slope": 2.0, 
        "curvature": "slight_curve", 
        "default_weather": "Cloudy", 
        "recommended_interventions": ["road_surface_treatment"]
    },
    "Barangay 2": {
        "coords": [14.155, 122.828],  # Approximate Lat/Lon
        "slope": 1.5, 
        "curvature": "intersection", 
        "default_weather": "Rainy", 
        "recommended_interventions": ["improved_street_lighting", "community_seminar"]
    },
    "Barangay 3": {
        "coords": [14.162, 122.826],  # Approximate Lat/Lon
        "slope": 3.0, 
        "curvature": "blind_curve", 
        "default_weather": "Cloudy", 
        "recommended_interventions": ["road_surface_treatment", "speed_checkpoint"]
    },
    "Barangay 4": {
        "coords": [14.148, 122.832],  # Approximate Lat/Lon
        "slope": 2.5, 
        "curvature": "intersection", 
        "default_weather": "Rainy", 
        "recommended_interventions": ["improved_street_lighting"]
    },
    "Barangay 5": {
        "coords": [14.165, 122.824],  # Approximate Lat/Lon
        "slope": 3.5, 
        "curvature": "blind_curve", 
        "default_weather": "Rainy", 
        "recommended_interventions": ["road_surface_treatment", "community_seminar"]
    }
}

# Intervention effects align with Materials & Methods (e.g., checkpoints, seminars, lighting upgrades)
intervention_effects = {
    "improved_street_lighting": {"lighting_override": "good", "reaction_multiplier": 0.75, "description": "Installation of additional LED street lights."},
    "road_surface_treatment": {"friction_bonus": 0.15, "road_condition_override": "dry", "description": "Application of anti-skid and pothole repairs."},
    "speed_checkpoint": {"speed_reduction": 0.25, "driver_risk_multiplier": 0.9, "description": "Random enforcement checkpoints to deter overspeeding."},
    "driver_safety_campaign": {"reaction_multiplier": 0.9, "driver_risk_multiplier": 0.95, "description": "Educational programs on defensive driving and Systems Theory interactions."},
    "community_seminar": {"reaction_multiplier": 0.95, "driver_risk_multiplier": 0.95, "description": "Barangay-wide awareness seminars targeting human factors."}
}

# Labo coordinates for map visualization
LABO_COORDINATES = {
    "Bayabas": (14.158, 122.825),
    "Main Highway": (14.15, 122.83),
    "Barangay 1": (14.16, 122.82),
    "Barangay 2": (14.155, 122.828),
    "Barangay 3": (14.162, 122.826),
    "Barangay 4": (14.148, 122.832),
    "Barangay 5": (14.165, 122.824)
}

# Full list of barangays for Labo, Camarines Norte (52)
LABO_BARANGAYS = [
    "Anahaw (Poblacion)",
    "Anameam",
    "Awitan",
    "Baay",
    "Bagacay",
    "Bagong Silang I",
    "Bagong Silang II",
    "Bagong Silang III",
    "Bakiad",
    "Bautista",
    "Bayabas",
    "Bayan-bayan",
    "Benit",
    "Bulhao",
    "Cabatuhan",
    "Cabusay",
    "Calabasa",
    "Canapawan",
    "Daguit",
    "Dalas",
    "Dumagmang",
    "Exciban",
    "Fundado",
    "Guinacutan",
    "Guisican",
    "Gumamela (Poblacion)",
    "Iberica",
    "Kalamunding (Poblacion)",
    "Lugui",
    "Mabilo I",
    "Mabilo II",
    "Macogon",
    "Mahawan-hawan",
    "Malangcao-Basud",
    "Malasugui",
    "Malatap",
    "Malaya",
    "Malibago",
    "Maot",
    "Masalong",
    "Matanlang",
    "Napaod",
    "Pag-asa",
    "Pangpang",
    "Pinya (Poblacion)",
    "San Antonio",
    "San Francisco (Poblacion)",
    "Santa Cruz",
    "Submakin",
    "Talobatib",
    "Tigbinan",
    "Tulay na Lupa",
]