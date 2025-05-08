# Import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
from matplotlib import rcParams

# Functions definition
def gaussian(x, sigma=0.01):
    """Function for Gaussian smearing."""
    return (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-x**2 / (2 * sigma**2))

def compute_dos(energies, sigma, grid_size):
    """Compute the density of states."""
    e_min = np.min(energies)
    e_max = np.max(energies)
    e_grid = np.arange(e_min, e_max, grid_size)
    dos = np.zeros_like(e_grid)
    for e in energies:
        dos += gaussian(e_grid - e, sigma)
    return e_grid, dos

def normalize_data(data):
    """Normalize data to the range [0, 1]."""
    return (data - np.min(data)) / (np.max(data) - np.min(data))

def remove_top_outliers(data):
    """Remove the top 0.05% of the data based on value."""
    threshold = np.percentile(data, 99.99)
    return data[data <= threshold]

# General style
matplotlib.rcParams.update({'font.size': 6, 'font.family': 'Arial'})
rcParams['axes.linewidth'] = 0.2
rcParams['mathtext.default'] = 'regular'
rcParams['ytick.minor.width'] = 0.2
rcParams['ytick.major.width'] = 0.2
rcParams['xtick.minor.width'] = 0.2
rcParams['xtick.major.width'] = 0.2
rcParams['axes.linewidth'] = 0.2

# Reading sheet names and filtering for "VO" prefix
all_sheet_names = pd.ExcelFile("C:\\Users\\zxf19\\Desktop\\KLMC.xlsx").sheet_names
vo_sheet_names = [sheet_name for sheet_name in all_sheet_names if sheet_name.startswith('VO')]

# Plot initialization
cm = 1/2.54
fig, ax = plt.subplots(figsize=(6*cm, 12*cm))

# Define the color map: Using 80% of PuBu, closer to Pu
colors = plt.cm.PuBu(np.linspace(0.3, 1, len(vo_sheet_names)))

# Parameters for DOS
offset = 0
fixed_offset = 1.5
binsize = 500
sigma = 0.0001

# For each sheet, compute the fully normalized DOS and plot with updated adaptive grid size, color, and labels
for idx, sheet_name in enumerate(vo_sheet_names):
    data = pd.read_excel("C:\\Users\\zxf19\\Desktop\\KLMC.xlsx", sheet_name=sheet_name)
    e_data = data['E'].dropna().values / 180
    e_data_no_outliers = remove_top_outliers(e_data)  # Removing top 0.01% outliers
    e_data_normalized = e_data_no_outliers - np.min(e_data_no_outliers)  # Normalize the energy values
    grid_size = (np.max(e_data_normalized) - np.min(e_data_normalized)) / binsize  # Compute adaptive grid size
    e_grid, dos = compute_dos(e_data_normalized, sigma=sigma, grid_size=grid_size)
    dos_normalized = normalize_data(dos)  # Normalize DOS values
    ax.plot(e_grid, dos_normalized + offset, linewidth=0.6, color=colors[idx])  # Using gradient color
    x_val = 2 - int(sheet_name.split("_")[1])/180
    label = f"CeO$_{{{round(x_val, 3):.3f}}}$"  # LaTeX for full subscript notation
    ax.text(e_grid[0]-7, offset + dos_normalized[0]+0.2, label, fontsize=7, verticalalignment='bottom', color=colors[idx])  # Label on the left
    offset += fixed_offset  # Using fixed offset for consistent spacing

# Styling the plot to match Nature style
ax.set_xlabel('Energy (eV)', fontsize=7)
ax.set_ylabel('DOS', fontsize=7)
ax.yaxis.set_minor_locator(MultipleLocator(1))
ax.yaxis.set_major_locator(MultipleLocator(3))
ax.xaxis.set_minor_locator(MultipleLocator(0.005))
ax.xaxis.set_major_locator(MultipleLocator(0.02))
# ax.set_ylim(0, 36)
ax.set_xlim(0, 0.18)
# ax.grid(True, which='both', linestyle='--', linewidth=0.5)

# Displaying the plot
plt.show()
fig.savefig('DOS_KLMC.png', dpi=600, bbox_inches='tight')
fig.savefig('DOS_KLMC.pdf', format='pdf', dpi=600, bbox_inches='tight')
