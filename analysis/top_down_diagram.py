import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

# ── Color map by file ─────────────────────────────────────────────────────────
FC = {
    'main.py':          ('#2980B9', 'PC Vision –\nmain.py'),
    'tracking.py':      ('#1ABC9C', 'PC Vision –\ntracking.py'),
    'UART.py':          ('#8E44AD', 'PC Vision –\nUART.py'),
    'main.s':           ('#E67E22', 'Firmware –\nmain.s'),
    'UART.s':           ('#C0392B', 'Firmware –\nUART.s'),
    'ADC.s':            ('#27AE60', 'Firmware –\nADC.s'),
    'ADC_To_Preload.s': ('#D4AC0D', 'Firmware –\nADC_To_Preload.s'),
    'DAC_Interrupt.s':  ('#884EA0', 'Firmware –\nDAC_Interrupt.s'),
    'system':           ('#2C3E50', ''),
}

NW, NH = 1.55, 0.62   # node box width, height

# ── Node registry: id → (cx, cy, label, file_key) ───────────────────────────
nodes = {
    # ROOT
    'root':     (11.0, 10.8, 'Aiming System',            'system'),

    # LEVEL 1  ── subsystems
    'pc':       ( 5.0,  9.4, 'PC Vision System',         'system'),
    'mcu':      (17.0,  9.4, 'PIC18 Firmware',           'system'),

    # LEVEL 2 ── PC
    'main_fn':  ( 2.0,  8.0, 'main()',                   'main.py'),
    'find_red': ( 5.2,  8.0, 'find_red\n_target_x()',    'tracking.py'),
    'uart_py':  ( 8.5,  8.0, 'UartLink',                 'UART.py'),

    # LEVEL 2 ── MCU
    'init':     (12.5,  8.0, 'Initialise',               'main.s'),
    'mloop':    (17.0,  8.0, 'main_loop()',               'main.s'),
    'pwm_isr':  (21.0,  8.0, 'PWM_Int_Hi()\n[Timer1 ISR]','DAC_Interrupt.s'),

    # LEVEL 3 ── PC
    'clamp':    ( 2.0,  6.5, 'clamp()',                  'main.py'),
    'us2pre':   ( 7.7,  6.5, 'us_to\n_preloads()',       'UART.py'),
    'sendpre':  ( 9.4,  6.5, 'send_preloads\n_us()',     'UART.py'),

    # LEVEL 3 ── MCU (Initialise children)
    'pwmsetup': (11.2,  6.5, 'PWM_Setup()',              'DAC_Interrupt.s'),
    'adcsetup': (12.8,  6.5, 'ADC_Setup()',              'ADC.s'),
    'usetup':   (14.4,  6.5, 'UART_Setup()',             'UART.s'),

    # LEVEL 3 ── MCU (main_loop children)
    'manual':   (15.8,  6.5, 'manual_mode()',            'main.s'),
    'auto':     (18.5,  6.5, 'auto_mode()',              'main.s'),

    # LEVEL 4 ── MCU (manual children)
    'adcread':  (14.8,  5.0, 'ADC_Read()',               'ADC.s'),
    'adc2pre':  (16.5,  5.0, 'ADC_To_Preloads\n_12bit()','ADC_To_Preload.s'),

    # LEVEL 4 ── MCU (auto children)
    'waitread': (17.7,  5.0, 'Wait_And\n_Read()',        'main.s'),
    'uart_rx':  (19.3,  5.0, 'UART_Read\n_Byte()',       'UART.s'),
    'uart_tx':  (21.0,  5.0, 'UART_Transmit\n_Byte()',   'UART.s'),
}

edges = [
    ('root', 'pc'), ('root', 'mcu'),
    # PC subtree
    ('pc', 'main_fn'), ('pc', 'find_red'), ('pc', 'uart_py'),
    ('main_fn', 'clamp'),
    ('uart_py', 'us2pre'), ('uart_py', 'sendpre'),
    # MCU subtree
    ('mcu', 'init'), ('mcu', 'mloop'), ('mcu', 'pwm_isr'),
    ('init', 'pwmsetup'), ('init', 'adcsetup'), ('init', 'usetup'),
    ('mloop', 'manual'), ('mloop', 'auto'),
    ('manual', 'adcread'), ('manual', 'adc2pre'),
    ('auto', 'waitread'), ('auto', 'uart_rx'), ('auto', 'uart_tx'),
]

# ── Draw ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(23, 10))
ax.set_xlim(0, 23)
ax.set_ylim(3.8, 12.0)
ax.axis('off')
fig.patch.set_facecolor('#F0F3F4')
ax.set_facecolor('#F0F3F4')

# Section backgrounds
from matplotlib.patches import FancyBboxPatch as FBP
ax.add_patch(FBP((0.2, 4.2), 9.8, 6.5,
    boxstyle='round,pad=0.1', lw=2, edgecolor='#2980B9',
    facecolor='#EBF5FB', zorder=0))
ax.text(5.1, 10.55, 'PC  (Python)', ha='center', fontsize=10,
        fontweight='bold', color='#1A5276')

ax.add_patch(FBP((10.4, 4.2), 12.2, 6.5,
    boxstyle='round,pad=0.1', lw=2, edgecolor='#E67E22',
    facecolor='#FEF9E7', zorder=0))
ax.text(16.5, 10.55, 'PIC18 Microcontroller  (Assembly)', ha='center',
        fontsize=10, fontweight='bold', color='#784212')


def draw_node(ax, cx, cy, label, fkey):
    color = FC[fkey][0]
    rect = FBP((cx - NW/2, cy - NH/2), NW, NH,
               boxstyle='round,pad=0.04,rounding_size=0.1',
               lw=1.5, edgecolor='white', facecolor=color, zorder=3)
    ax.add_patch(rect)
    n_lines = label.count('\n') + 1
    fs = 7.8 if n_lines == 1 else 7.2
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color='white', zorder=4,
            linespacing=1.25)


def draw_edge(ax, parent_id, child_id):
    px, py, *_ = nodes[parent_id]
    cx, cy, *_ = nodes[child_id]
    # start from bottom of parent, end at top of child
    y_start = py - NH/2
    y_end   = cy + NH/2
    ax.annotate('', xy=(cx, y_end), xytext=(px, y_start),
                arrowprops=dict(arrowstyle='->', color='#555555',
                                lw=1.3, connectionstyle='arc3,rad=0.0'),
                zorder=2)


# Draw edges first (behind nodes)
for p, c in edges:
    draw_edge(ax, p, c)

# Draw nodes
for nid, (cx, cy, label, fkey) in nodes.items():
    draw_node(ax, cx, cy, label, fkey)

# Title
ax.text(11.5, 11.65, 'Top-Down Modular Design — Aiming System',
        ha='center', va='center', fontsize=15, fontweight='bold',
        color='#1A252F')

# ── Legend ───────────────────────────────────────────────────────────────────
legend_items = [(v[0], v[1]) for k, v in FC.items() if v[1]]
lx, ly = 0.35, 4.05
ax.text(lx, ly + 0.08, 'File colour key:', fontsize=8,
        fontweight='bold', color='#333', va='bottom')
for i, (col, label) in enumerate(legend_items):
    bx = lx + i * 2.82
    rect = FBP((bx, ly - 0.42), 2.6, 0.38,
               boxstyle='round,pad=0.03', lw=0,
               facecolor=col, zorder=5)
    ax.add_patch(rect)
    ax.text(bx + 1.3, ly - 0.235, label.replace('\n', '  '),
            ha='center', va='center', fontsize=6.5,
            color='white', fontweight='bold', zorder=6)

# Note: find_red_target_x is a leaf (all logic internal to tracking.py)
ax.text(5.2, 7.25, '(internal: HSV mask +\nmorphology + contours)',
        ha='center', va='top', fontsize=6.5, color='#1ABC9C',
        style='italic')

plt.tight_layout(pad=0.3)
plt.savefig('top_down_diagram.png', dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print("Saved top_down_diagram.png")
plt.show()
