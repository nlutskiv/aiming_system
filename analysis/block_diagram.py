import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

fig, ax = plt.subplots(figsize=(15.5, 8))
ax.set_xlim(0, 15.5)
ax.set_ylim(2.5, 11.0)
ax.axis('off')
fig.patch.set_facecolor('#F8F9FA')

# ── helpers ──────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, label, sublabel=None,
        fc='#2C3E50', ec='white', tc='white', fs=10, subfs=8, radius=0.15):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0.05,rounding_size={radius}",
                          linewidth=1.5, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(rect)
    ty = y + h/2 + (0.15 if sublabel else 0)
    ax.text(x + w/2, ty, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color=tc, zorder=4)
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.22, sublabel, ha='center', va='center',
                fontsize=subfs, color=tc, style='italic', zorder=4)

def arrow(ax, x1, y1, x2, y2, color='#555555', both=False, lw=1.8):
    style = '<->' if both else '->'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle='arc3,rad=0.0'),
                zorder=2)

def label_arrow(ax, x, y, text, fs=7.5, color='#333333'):
    ax.text(x, y, text, ha='center', va='center', fontsize=fs,
            color=color, zorder=5,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION BACKGROUNDS
# ══════════════════════════════════════════════════════════════════════════════
# PC section
pc_bg = FancyBboxPatch((0.3, 3.3), 5.4, 6.2,
                        boxstyle="round,pad=0.1", linewidth=2,
                        edgecolor='#3498DB', facecolor='#EBF5FB', zorder=1)
ax.add_patch(pc_bg)
ax.text(3.0, 9.3, 'PC  (Python)', ha='center', va='center',
        fontsize=11, fontweight='bold', color='#2980B9')

# MCU section
mcu_bg = FancyBboxPatch((7.3, 3.3), 5.3, 6.2,
                         boxstyle="round,pad=0.1", linewidth=2,
                         edgecolor='#E67E22', facecolor='#FEF9E7', zorder=1)
ax.add_patch(mcu_bg)
ax.text(9.95, 9.3, 'PIC18  Microcontroller', ha='center', va='center',
        fontsize=11, fontweight='bold', color='#D35400')

# ══════════════════════════════════════════════════════════════════════════════
# PC BLOCKS
# ══════════════════════════════════════════════════════════════════════════════
# Camera
box(ax, 0.6, 7.2, 2.2, 1.1, 'USB Camera', 'Frame capture', fc='#1ABC9C')
# OpenCV Tracker
box(ax, 0.6, 5.6, 2.2, 1.1, 'OpenCV', 'Red-target detection', fc='#2980B9')
# P-Controller
box(ax, 3.0, 5.6, 2.3, 1.1, 'P-Controller', f'Kp = 0.15', fc='#8E44AD')
# UART Link (Python)
box(ax, 3.0, 3.8, 2.3, 1.1, 'UART Link', 'Serial @ 9600 baud', fc='#C0392B')

# ── PC internal arrows ───────────────────────────────────────────────────────
arrow(ax, 1.7, 7.2, 1.7, 6.7)          # Camera → OpenCV
label_arrow(ax, 2.35, 6.97, 'BGR frame')
arrow(ax, 2.8, 6.15, 3.0, 6.15)        # OpenCV → P-Controller
label_arrow(ax, 2.9, 6.47, 'target_x')
arrow(ax, 4.15, 5.6, 4.15, 4.9)        # P-Controller → UART Link
label_arrow(ax, 4.85, 5.25, 'pulse_us')

# Sync back arrow (UART → P-controller, bumpless transfer)
ax.annotate('', xy=(3.1, 4.9), xytext=(3.1, 5.6),
            arrowprops=dict(arrowstyle='<-', color='#E74C3C', lw=1.5,
                            connectionstyle='arc3,rad=0.0'), zorder=2)
label_arrow(ax, 2.35, 5.27, 'sync\n(0xAA)', fs=7)

# ══════════════════════════════════════════════════════════════════════════════
# UART SERIAL LINK  (PC ↔ MCU)
# ══════════════════════════════════════════════════════════════════════════════
box(ax, 5.85, 3.95, 1.3, 0.85, 'USB/\nSerial', fc='#7F8C8D', fs=8.5)
arrow(ax, 5.3, 4.35, 5.85, 4.35, both=True, color='#C0392B', lw=2.2)
arrow(ax, 7.15, 4.35, 7.8, 4.35, both=True, color='#C0392B', lw=2.2)
label_arrow(ax, 6.5, 4.72, '0xAA 0x55\npkt (6 B)', fs=7)

# ══════════════════════════════════════════════════════════════════════════════
# MCU BLOCKS
# ══════════════════════════════════════════════════════════════════════════════
# UART module
box(ax, 7.8, 3.8, 2.0, 1.1, 'UART Module', 'RX / TX', fc='#C0392B')
# Timer1 PWM
box(ax, 7.8, 5.8, 2.0, 1.1, 'Timer1', 'ISR-driven PWM', fc='#E67E22')
# PORTJ
box(ax, 7.8, 7.5, 2.0, 1.0, 'PORTJ  (RJ0)', 'PWM output', fc='#D35400')
# ADC
box(ax, 10.3, 3.8, 2.0, 1.1, 'ADC', '10/12-bit read', fc='#16A085')
# Mode switch logic
box(ax, 10.3, 5.8, 2.0, 1.1, 'Mode Logic', 'Manual / Auto', fc='#27AE60')
# PORTB
box(ax, 10.3, 7.5, 2.0, 1.0, 'PORTB  (RB0)', 'Mode switch input', fc='#1E8449')

# ── MCU internal arrows ──────────────────────────────────────────────────────
# UART → Mode Logic
arrow(ax, 8.8, 4.9,  8.8, 5.8)
label_arrow(ax, 9.5, 5.35, 'preloads')
# ADC → Mode Logic
arrow(ax, 11.3, 4.9, 11.3, 5.8)
label_arrow(ax, 11.95, 5.35, 'ADC val')
# PORTB → Mode Logic
arrow(ax, 11.3, 7.5, 11.3, 6.9)
label_arrow(ax, 11.95, 7.17, 'btn state')
# Mode Logic → Timer1
arrow(ax, 10.3, 6.35, 9.8, 6.35)
label_arrow(ax, 10.05, 6.7, 'pre_hi/lo')
# Timer1 → PORTJ
arrow(ax, 8.8, 6.9, 8.8, 7.5)
label_arrow(ax, 9.5, 7.17, 'PWM pulse')

# ══════════════════════════════════════════════════════════════════════════════
# EXTERNAL PERIPHERALS
# ══════════════════════════════════════════════════════════════════════════════
# Servo
box(ax, 7.5, 10.0, 2.5, 0.8, 'Servo Motor', fc='#884EA0', radius=0.12)
arrow(ax, 8.8, 8.5, 8.8, 10.0, color='#884EA0', lw=2)
label_arrow(ax, 9.6, 9.65, 'PWM\nsignal', fs=7)

# Potentiometer
box(ax, 13.0, 3.95, 2.2, 0.8, 'Potentiometer', fc='#117A65', radius=0.12)
arrow(ax, 13.0, 4.35, 12.3, 4.35, color='#117A65', lw=2)
label_arrow(ax, 12.65, 4.7, 'analog\nvoltage', fs=7)

# Push button
box(ax, 13.0, 7.6, 2.2, 0.8, 'Switch', fc='#196F3D', radius=0.12)
arrow(ax, 13.0, 8.0, 12.3, 8.0, color='#196F3D', lw=2)
label_arrow(ax, 12.65, 8.35, 'digital\nin', fs=7)

# Power supply note
ax.text(0.5, 2.65, 'Power: 5 V board supply  |  9600 baud UART  |  Timer1 tick = 0.5 µs  |  PWM: 20 ms period',
        fontsize=8, color='#555555', style='italic')

# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
plt.tight_layout()
plt.savefig(os.path.join(_HERE, 'system_block_diagram.png'), dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print("Saved system_block_diagram.png")
plt.show()
