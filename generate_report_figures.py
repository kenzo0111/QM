import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure directory exists
os.makedirs('report_figures', exist_ok=True)

# --- Figure 4.1: Historical vs Simulated Severity ---
labels = ['Severe', 'Moderate', 'Minor/None']
historical = [90.9, 9.1, 0.0]
simulated = [69.0, 11.0, 20.0]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5))
rects1 = ax.bar(x - width/2, historical, width, label='Historical Records', color='#4C72B0')
rects2 = ax.bar(x + width/2, simulated, width, label='Simulated Model', color='#55A868')

ax.set_ylabel('Percentage (%)')
ax.set_title('Comparison of Accident Severity Distributions')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
ax.bar_label(rects1, padding=3, fmt='%.1f%%')
ax.bar_label(rects2, padding=3, fmt='%.1f%%')
ax.set_ylim(0, 100)
plt.tight_layout()
plt.savefig('report_figures/fig_4_1_severity_comparison.png')
print("Generated Figure 4.1: report_figures/fig_4_1_severity_comparison.png")
plt.close()

# --- Figure 4.3: Intervention Analysis (Comparison) ---
# We will use a grouped bar chart for Impact Force as it's the most dramatic
labels = ['Baseline', 'With Intervention']
impact_force = [894337, 688599]

fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(labels, impact_force, color=['#C44E52', '#8172B3'], width=0.5)

ax.set_ylabel('Mean Impact Force (Newtons)')
ax.set_title('Effect of Interventions on Impact Force')
ax.bar_label(bars, fmt='{:,.0f} N')
plt.tight_layout()
plt.savefig('report_figures/fig_4_3_impact_force_reduction.png')
print("Generated Figure 4.3: report_figures/fig_4_3_impact_force_reduction.png")
plt.close()
