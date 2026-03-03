import requests
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import time

# --- PARAMETER CE-TENG (CHARGE-EXCITED) SKALA LAPANGAN ---
LAT, LON = -8.018, 110.332
SLOPE = 0.05                
# Nilai SIGMA ditingkatkan drastis karena mekanisme Charge-Excitation (dari 60uC ke 1.2mC)
SIGMA_CE = 1.2e-3           # Kerapatan muatan tinggi hasil eksitasi (C/m^2)
AREA_BASE = 0.15            
D_GAP = 0.005               
EPSILON_0 = 8.854e-12       
LAYERS_TO_COMPARE = [1, 10, 20] 

def fetch_wave_data():
    try:
        url = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT}&longitude={LON}&current=wave_height,wave_period"
        res = requests.get(url, timeout=5).json()
        return res['current']['wave_height'], res['current']['wave_period']
    except:
        return 1.8, 9.0 

# --- SETUP LAYOUT (3D di Kiri, Dashboard di Kanan) ---
plt.style.use('dark_background')
fig = plt.figure(figsize=(16, 8))
ax_3d = fig.add_subplot(121, projection='3d')
ax_text = fig.add_subplot(122)
ax_text.axis('off')

time_steps = 20
power_matrix = np.zeros((len(LAYERS_TO_COMPARE), time_steps))
x_axis = np.arange(time_steps)
y_axis = np.array(LAYERS_TO_COMPARE)
X, Y = np.meshgrid(x_axis, y_axis)

def update(frame):
    h_s, t_p = fetch_wave_data()
    timestamp = time.strftime('%H:%M:%S')

    # --- LOGIKA FISIKA CE-TENG ---
    h_rand = np.random.rayleigh(h_s / 1.414)
    l_0 = (9.81 * (t_p**2)) / (2 * np.pi)
    xi = SLOPE / np.sqrt(h_rand / l_0)
    
    c_imp = 2.8 if 0.5 <= xi <= 3.3 else 1.3
    v_internal = (h_rand * c_imp) / t_p
    
    # Tegangan Dasar (Voc) dengan SIGMA_CE
    v_oc_base = (SIGMA_CE * D_GAP) / EPSILON_0
    i_sc_base = SIGMA_CE * AREA_BASE * v_internal

    ax_3d.clear()
    ax_text.clear()
    ax_text.axis('off')
    
    for i, n in enumerate(LAYERS_TO_COMPARE):
        i_sc_total = n * i_sc_base
        total_power = v_oc_base * i_sc_total
        power_matrix[i, :-1] = power_matrix[i, 1:]
        power_matrix[i, -1] = total_power

    # RENDER 3D
    ax_3d.plot_surface(X, Y, power_matrix, cmap='plasma', edgecolor='none', alpha=0.85)
    ax_3d.set_title("Visualisasi Power Output CE-TENG (Skala Watt)", fontsize=12)
    ax_3d.set_zlabel('Power (Watt)')
    ax_3d.view_init(elev=25, azim=-60)

    # DASHBOARD TEXT
    info_header = "DASHBOARD CE-TENG PARANGTRITIS\n" + "="*35 + "\n"
    info_body = (
        f"Mekanisme: Charge-Excitation (CE)\n"
        f"Sigma (Excited) : {SIGMA_CE*1000:.1f} mC/m^2\n\n"
        f"Wave Info:\n"
        f"  Indiv Height (H): {h_rand:.2f} m\n"
        f"  Period (Tp)     : {t_p} s\n\n"
        f"Electrical Info (Output Real):\n"
        f"  Max Power (n=20): {np.max(power_matrix):.2f} W\n"
        f"  Total Current   : {np.max(power_matrix)/v_oc_base*1000:.2f} mA\n"
        f"  Base Voc        : {v_oc_base/1000:.1f} kV\n"
        f"  Timestamp       : {timestamp}"
    )
    
    ax_text.text(0.05, 0.5, info_header + info_body, 
                color='yellow', fontsize=11, family='monospace', 
                fontweight='bold', verticalalignment='center',
                bbox=dict(facecolor='black', alpha=0.5, edgecolor='yellow', boxstyle='round,pad=2'))

plt.tight_layout()
ani = FuncAnimation(fig, update, interval=5000, cache_frame_data=False)
plt.show()