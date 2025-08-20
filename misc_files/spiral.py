import numpy as np
import matplotlib.pyplot as plt

theta = np.linspace(0, 2 * np.pi, 1000)  # 1 FULL TURN (360°)

# Constants
phi = (1 + np.sqrt(5)) / 2  # ≈1.618
rho = 1.324718  # Plastic number

# Symmetric formulas
r_golden = phi ** (2 * theta / np.pi)  # Growth per 90° turn
r_plastic = rho ** (2 * theta / np.pi)  # Growth per 90° turn

plt.figure(figsize=(10, 8))
ax = plt.subplot(111, polar=True)

# Plot spirals
ax.plot(theta, r_golden, color='#CCAD00', lw=2, label='Golden Spiral (φ=1.618)')  # Dark golden color
ax.plot(theta, r_plastic, color='blue', lw=2, label='Plastic Spiral (ρ=1.325)')  # Blue color

# Mark 25% of the last 90-degree arc of the plastic spiral as red
theta_red = np.linspace(2 * np.pi - np.pi / 8, 2 * np.pi, 1000)
r_plastic_red = rho ** (2 * theta_red / np.pi)
ax.plot(theta_red, r_plastic_red, color='red', lw=4) # Changed lw from 2 to 4

# LIGHTENED CONCENTRIC RINGS (hex #f0f0f0)
ax.grid(color='#b0b0b0', alpha=0.8, linestyle='-', linewidth=0.8)

# Angular labels
ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
ax.set_xticklabels(['0°', '90°', '180°', '270°'])
ax.set_yticklabels([])  # Hide radial values

# Add legend for Plastic Correction Unit (rho - 1)
ax.plot([], [], 'red', label=r'Plastic Correction Unit $(\rho-1)$')

# Enhanced legend
legend = ax.legend(
    loc='upper right',
    bbox_to_anchor=(1.25, 1.0),
    prop={'size': 12, 'weight': 'bold'},
    framealpha=0.95,
)

plt.tight_layout()
plt.savefig('spiral_comparison.png', dpi=300, bbox_inches='tight')  # CHANGED FILENAME