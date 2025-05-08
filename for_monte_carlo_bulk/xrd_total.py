# Import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
from matplotlib import rcParams
import matplotlib.colors as mcolors
import seaborn as sns
import os

#def normalize_data(data):
#    """Normalize data to the range [0, 1]."""
#    return (data - np.min(data)) / (np.max(data) - np.min(data))

def filter_low_saturation_colors(cmap, threshold=0.3):
    colors = cmap(np.linspace(0, 1, 256))
    colors_hsv = mcolors.rgb_to_hsv(colors[:, :3])
    high_saturation_colors = colors[colors_hsv[:, 1] > threshold]
    if len(high_saturation_colors) < 2:
        raise ValueError("Filtered colors are too few to create a colormap!")
    new_cmap = mcolors.LinearSegmentedColormap.from_list("filtered_cmap", high_saturation_colors)
    return new_cmap

# General style
matplotlib.rcParams.update({'font.size': 6, 'font.family': 'DejaVu Sans'})
rcParams['axes.linewidth'] = 0.2
rcParams['mathtext.default'] = 'regular'
rcParams['ytick.minor.width'] = 0.2
rcParams['ytick.major.width'] = 0.2
rcParams['xtick.minor.width'] = 0.2
rcParams['xtick.major.width'] = 0.2
rcParams['axes.linewidth'] = 0.2

# Read files
files = [os.path.join(folder, 'xrd_weighted.txt') for folder in os.listdir('.') if os.path.isdir(folder) and folder.startswith('VO_')]

dfs = {}  # Change to a dictionary

# Read and process each file
for file in files:
    df = pd.read_csv(file, sep=',')
    
    # Normalize the Total_Weighted_Intensity column
    df['Normalized_Total_Weighted_Intensity'] = df['Total_Weighted_Intensity'] / df['Total_Weighted_Intensity'].max()
    for col in df.columns[1:]:
        df[col] = df[col] / df['Total_Weighted_Intensity'].max()

    directory_name = os.path.basename(os.path.dirname(file))  # Extracting the directory name
    dfs[directory_name] = df  # Use the directory name as the key
    
# Sort dfs by the number after 'VO_'
dfs = {k: v for k, v in sorted(dfs.items(), key=lambda item: int(item[0].split('_')[1]))}

# colours
newcolormap = filter_low_saturation_colors(sns.color_palette("rocket", as_cmap=True), threshold=0.3)
vo_sheet_names = [sheet_name for sheet_name in dfs]
colors = newcolormap(np.linspace(0.00, 0.55, len(vo_sheet_names)))

# Plot and parameters
cm = 1/2.54
fig, ax = plt.subplots(figsize=(8*cm, 10*cm))
intitial_offset = 0
offset = 0.1
idx = 0

# For loop 
for dirname, df in dfs.items(): 
    print(dirname)
    print(df.head())
    ax.plot(df['Two_Theta'], df['Normalized_Total_Weighted_Intensity'] + intitial_offset, label=dirname, lw=0.4, color=colors[idx])
    min_intensity = df.iloc[:, 2:-1].min(axis=1)
    max_intensity = df.iloc[:, 2:-1].max(axis=1)
    ax.fill_between(df["Two_Theta"], min_intensity + intitial_offset, max_intensity + intitial_offset, alpha=0.3, color=colors[idx], linewidth=0)
    # name
    nonstoi = 2 - int(dirname.split("_")[1])/180  # Use `dirname` instead of `df`
    label = f"CeO$_{{{round(nonstoi, 3):.3f}}}$"  # LaTeX for full subscript notation
    ax.text(df['Two_Theta'].iloc[0]-2, intitial_offset, label, fontsize=6, verticalalignment='bottom', color=colors[idx], ha='right')  # Label on the left
    # loop
    intitial_offset += offset
    idx += 1

ax.set_xlabel("2θ (°)", fontsize=7)
ax.set_ylabel("Intensity", fontsize=7, labelpad=30)
ax.set_xlim(0, 120)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_locator(MultipleLocator(20))
ax.xaxis.set_minor_locator(MultipleLocator(5))
ax.yaxis.set_ticks([])
ax.yaxis.set_ticklabels([])
# ax.spines['left'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['top'].set_visible(False)

# Get current x-axis major and minor ticks and labels
# y_min, y_max = ax.get_ylim()
# major_xticks = ax.get_xticks()
# 
# # Draw the x-axis lines with major and minor ticks for each offset
# for y in np.arange(y_min, y_max-2*offset, offset):
#     ax.axhline(y=y, color='black', linestyle='-', linewidth=0.2, zorder=0)
#     # Major ticks
# for y in np.arange(y_min, y_max-2*offset, offset):
#     for xtick in major_xticks:
#         ax.plot([xtick, xtick], [y - 0.2, y], color='black', linewidth=0.2, zorder=0)

fig.subplots_adjust(left=0.3)

ax.grid(True, which='major', linewidth=0.2, color='black')
# ax.grid(True, which='minor', axis='y', linewidth=0.2)

# Displaying the plot
# plt.show()
fig.savefig('XRD_total.png', dpi=600, bbox_inches='tight')
fig.savefig('XRD_total.pdf', format='pdf', dpi=600, bbox_inches='tight')