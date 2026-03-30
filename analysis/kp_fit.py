import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar

# ── load data ────────────────────────────────────────────────────────────────
kp_vals, mean_times, n_obs, std_devs = [], [], [], []

with open("DynamicTests.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["K_P (speed)"] and row["mean time"]:
            kp_vals.append(float(row["K_P (speed)"]))
            mean_times.append(float(row["mean time"]))
            # collect individual repeat measurements (columns 2-6)
            reps = [float(row[k]) for k in list(row.keys())[1:6]
                    if row[k].strip()]
            n_obs.append(len(reps))
            # std dev only meaningful with >1 repeat; else None
            std_devs.append(np.std(reps, ddof=1) if len(reps) > 1 else None)

kp   = np.array(kp_vals)
t    = np.array(mean_times)
w    = np.array(n_obs, dtype=float)          # weight = number of repeat measurements
stds = np.array([s if s is not None else 0.0 for s in std_devs])
has_err = np.array([s is not None for s in std_devs])  # mask for points with error bars

# ── polynomial fit (degree 4, weighted) ─────────────────────────────────────
deg = 4
coeffs = np.polyfit(kp, t, deg=deg, w=w)
poly   = np.poly1d(coeffs)

# find the minimum of the polynomial in the sampled range
result  = minimize_scalar(poly, bounds=(kp.min(), kp.max()), method='bounded')
kp_opt  = result.x
t_opt   = result.fun

print(f"Polynomial degree : {deg}")
print(f"Optimal Kp        : {kp_opt:.4f}")
print(f"Predicted min time: {t_opt:.3f} s")
print(f"Closest measured  : Kp={kp[np.argmin(t)]:.3f}, t={t.min():.3f} s")

# ── plot ─────────────────────────────────────────────────────────────────────
kp_smooth = np.linspace(kp.min(), kp.max(), 400)
t_smooth  = poly(kp_smooth)

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('#F8F9FA')
ax.set_facecolor('#F8F9FA')

# error bars for points with multiple repeats
ax.errorbar(kp[has_err], t[has_err], yerr=stds[has_err],
            fmt='none', ecolor='#2980B9', elinewidth=1.4,
            capsize=4, capthick=1.4, zorder=4, alpha=0.7,
            label='±1 std dev (repeated trials)')

# scatter: size proportional to number of repeats
sc = ax.scatter(kp, t, s=w*25+20, c='#2980B9', zorder=5,
                label='Measured mean time\n(dot size ∝ repeats)')

# fit curve
ax.plot(kp_smooth, t_smooth, '-', color='#E74C3C', lw=2,
        label=f'Degree-{deg} polynomial fit')

# minimum marker
ax.axvline(kp_opt, color='#E67E22', lw=1.5, ls='--', alpha=0.8)
ax.axhline(t_opt,  color='#E67E22', lw=1.5, ls='--', alpha=0.8)
ax.scatter([kp_opt], [t_opt], s=120, color='#E67E22', zorder=6,
           label=f'Fitted minimum: Kp = {kp_opt:.3f}, t = {t_opt:.2f} s')

# annotate optimal
ax.annotate(f'  Kp* = {kp_opt:.3f}\n  t* = {t_opt:.2f} s',
            xy=(kp_opt, t_opt), xytext=(kp_opt + 0.03, t_opt + 1.5),
            fontsize=9, color='#D35400',
            arrowprops=dict(arrowstyle='->', color='#D35400', lw=1.2))

ax.set_xlabel('K_P', fontsize=12)
ax.set_ylabel('Mean Time to Acquire Target (s)', fontsize=12)
ax.set_title('K_P Tuning — Polynomial Fit & Optimal Value', fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.4)
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig('kp_fit.png', dpi=150, bbox_inches='tight')
print("Saved kp_fit.png")
plt.show()
