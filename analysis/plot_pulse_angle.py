import csv
import numpy as np
import matplotlib.pyplot as plt

pulse_widths = []
angles = []

with open("PulseToAngle.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["Pulse Width"] and row["Angle"]:
            pulse_widths.append(float(row["Pulse Width"]))
            angles.append(float(row["Angle"]))

m, b = np.polyfit(pulse_widths, angles, 1)
fit_x = np.linspace(min(pulse_widths), max(pulse_widths), 100)

plt.figure(figsize=(8, 5))
plt.errorbar(pulse_widths, angles, yerr=0.1, fmt="o", capsize=4, label="Angle ± 0.1°")
plt.plot(fit_x, m * fit_x + b, label=f"Fit: y = {m:.2f}x + {b:.2f}")

plt.xlabel("Pulse Width (ms)")
plt.ylabel("Angle (°)")
plt.title("Pulse Width vs Angle")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("pulse_angle_plot.png", dpi=150)
plt.show()
