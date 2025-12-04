
import pandas as pd
import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from analysis import run_monte_carlo_simulations, run_monte_carlo_intervention_analysis

def analyze_historical_data():
    print("--- Historical Data Analysis ---")
    try:
        df = pd.read_csv('accident_data.csv')
        print(f"Total Historical Records: {len(df)}")
        print("\nSeverity Distribution:")
        print(df['severity'].value_counts(normalize=True) * 100)
        print("\nTop Causes:")
        print(df['cause'].value_counts().head(3))
    except Exception as e:
        print(f"Error reading accident_data.csv: {e}")

def run_simulations():
    print("\n--- Monte Carlo Simulation Results (N=100) ---")
    results = run_monte_carlo_simulations(runs=100)
    print("Simulated Severity Distribution:")
    for k, v in results.items():
        if k not in ['average_risk_score', 'average_impact_force']:
            print(f"  {k}: {v}")
    print(f"Average Risk Score: {results.get('average_risk_score')}")
    print(f"Average Impact Force: {results.get('average_impact_force'):.2f} N")

def run_intervention_analysis():
    print("\n--- Counterfactual Intervention Analysis (N=50 pairs) ---")
    results = run_monte_carlo_intervention_analysis(runs=50)
    
    base = results['baseline']
    inter = results['intervention']
    
    print("Baseline Average Risk Score:", base.get('average_risk_score'))
    print("Intervention Average Risk Score:", inter.get('average_risk_score'))
    
    risk_reduction = ((base.get('average_risk_score') - inter.get('average_risk_score')) / base.get('average_risk_score')) * 100
    print(f"Risk Reduction: {risk_reduction:.2f}%")
    
    print("Baseline Avg Impact Force:", base.get('average_impact_force'))
    print("Intervention Avg Impact Force:", inter.get('average_impact_force'))
    
    force_reduction = ((base.get('average_impact_force') - inter.get('average_impact_force')) / base.get('average_impact_force')) * 100
    print(f"Impact Force Reduction: {force_reduction:.2f}%")

if __name__ == "__main__":
    analyze_historical_data()
    run_simulations()
    run_intervention_analysis()
