import csv
import numpy as np
import matplotlib.pyplot as plt

kp = []
mean_time = []

with open("DynamicTests.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["K_P (speed)"] and row["mean time"]:
            kp.append(float(row["K_P (speed)"]))
            mean_time.append(float(row["mean time"]))

plt.figure(figsize=(8, 5))
plt.plot(kp, mean_time, "o", label="Data")

plt.xlabel("K_P")
plt.ylabel("Mean Time (s)")
plt.title("K_P vs Mean Time")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("kp_time_plot.png", dpi=150)
plt.show()
