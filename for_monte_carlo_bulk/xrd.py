import pandas as pd
import os
import sys
import numpy as np
import matplotlib.pyplot as plt  # Plotting
from matplotlib import rcParams
import matplotlib
import Dans_Diffraction as dif
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
from concurrent.futures import ProcessPoolExecutor

################################ sort energies ##########################################

# Read the data from the file
data = pd.read_csv("energy_filtered.txt", sep=" ", skipinitialspace=True)

# Sort the data based on the first column and take the first 10 lines
sorted_data = data.sort_values(by=data.columns[0], ascending=True).head(10)

# Print the sorted data
print(sorted_data)

# Get the index values (line names) from the sorted_data dataframe
index_values = sorted_data.index.tolist()
print(index_values)

# Save the sorted data to "energy_filter_10.txt" including the index (line names)
sorted_data.to_csv("energy_filter_10.txt", sep=" ", index=True)

################################ xrd ##########################################

# Setting up plotting parameters
matplotlib.rcParams.update({'font.size': 6, 'font.family': 'DejaVu Sans'})
plt.rcParams['axes.linewidth'] = 0.2
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['ytick.minor.width'] = 0.2
plt.rcParams['ytick.major.width'] = 0.2
plt.rcParams['xtick.minor.width'] = 0.2
plt.rcParams['xtick.major.width'] = 0.2
plt.rcParams['axes.linewidth'] = 0.2

# Define the XRD function
def perform_xrd():
    cm = 1/2.54
    fig, ax = plt.subplots(figsize=(16*cm, 8*cm))
    
    # import cif
    f = 'b.cif'
    xtl = dif.Crystal(f)
    
    energy_kev = dif.fc.wave2energy(1.5498)  # 8 keV
    q, intensity, reflections = xtl.Scatter.powder('xray', units='Q', energy_kev=energy_kev, peak_width=0.01, background=0)
    
    # convert wavevector, q=2pi/d to two-theta:
    twotheta = dif.fc.cal2theta(q, energy_kev)
    
    # save data as csv file
    head = '%s\nx-ray powder diffraction energy=%6.3f keV\n two-theta, intensity' % (xtl.name, energy_kev)
    np.savetxt('powder.csv', (twotheta, intensity), delimiter=',', header=head)
    
    # plot the spectra
    ax.plot(twotheta, intensity, '-', lw=0.4, color='#304697')
    ax.set_xlabel("2θ (°)", fontsize=7)
    ax.set_ylabel("Intensity", fontsize=7)
    ax.set_xlim(0, 120)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.xaxis.set_minor_locator(MultipleLocator(5))
    
    fig.savefig('xrd.png', dpi=1200, bbox_inches='tight')
    fig.savefig('xrd.pdf', format='pdf', dpi=1200, bbox_inches='tight')
    
    print('XRD ok for directory:', os.getcwd())

# Define a wrapper function that sets the working directory and then performs XRD
def parallel_xrd(directory):
    os.chdir(directory)
    perform_xrd()
    os.chdir('..')  # return to the parent directory

# Use ProcessPoolExecutor to parallelize the XRD function across directories
with ProcessPoolExecutor(max_workers=10) as executor:
    executor.map(parallel_xrd, index_values)
    
################################ statistics ##########################################

# Read the directory names and corresponding weights from sorted_data
directories = sorted_data.index.tolist()
weights = sorted_data["Weight"].tolist()
sum_of_weights = sorted_data["Weight"].sum()

# Initialize a list to store weighted intensity data for each directory
all_weighted_intensity = []

# Initialize total_weighted_intensity as an array (you may want to initialize it to zeros with the same shape as your data)
total_weighted_intensity = None

# Loop through each directory and process the powder.csv file
for directory, weight in zip(directories, weights):
    # Read the powder.csv file
    data = np.loadtxt(os.path.join(directory, 'powder.csv'), delimiter=',', skiprows=3)
    two_theta, intensity = data  # Define 'intensity' here after loading data
    
    # Weight the intensity
    weighted_intensity = intensity * weight
    
    # Add the intensity to the list
    all_weighted_intensity.append(intensity)
    
    # If total_weighted_intensity is None (first iteration), initialize it. Else, add to it.
    if total_weighted_intensity is None:
        total_weighted_intensity = weighted_intensity
    else:
        total_weighted_intensity += weighted_intensity

# Divided by sum
total_weighted_intensity = total_weighted_intensity / sum_of_weights

# Convert the list of weighted_intensity arrays into a 2D array
all_weighted_intensity = np.column_stack(all_weighted_intensity)

# Create a header for the columns, including "Two_Theta" and "Total_Weighted_Intensity"
header = "Two_Theta," + ",".join([f"Intensity{i+1}" for i in range(len(directories))]) + ",Total_Weighted_Intensity"

# Stack the Two_Theta and total_weighted_intensity horizontally
output_data = np.column_stack([two_theta, all_weighted_intensity, total_weighted_intensity])

# Write the data to xrd_weighted.txt
np.savetxt('xrd_weighted.txt', output_data, delimiter=',', header=header, comments="")

print('Weighted XRD data saved to weighted_xrd.txt')
print('Done')

############################Final plot#################################################

# plot the spectra
cm = 1/2.54
fig1, ax1 = plt.subplots(figsize=(16*cm, 8*cm))
data2 = pd.read_csv("xrd_weighted.txt", skipinitialspace=True)

# Plot the shaded region representing the range of XRD intensities
min_intensity = data2.iloc[:, 2:-1].min(axis=1)
max_intensity = data2.iloc[:, 2:-1].max(axis=1)
ax1.fill_between(data2["Two_Theta"], min_intensity, max_intensity, alpha=0.3, color='#304697', linewidth=0)

# Plot the total weighted intensity
ax1.plot(data2["Two_Theta"], data2["Total_Weighted_Intensity"], '-', lw=0.4, color='#304697')

ax1.set_xlabel("2θ (°)", fontsize=7)
ax1.set_ylabel("Intensity", fontsize=7)
ax1.set_xlim(0, 120)
ax1.set_ylim(bottom=0)
ax1.xaxis.set_major_locator(MultipleLocator(20))
ax1.xaxis.set_minor_locator(MultipleLocator(5))
plt.gca().set_yticklabels([])
fig1.savefig('xrd.png', dpi=1200, bbox_inches='tight')
fig1.savefig('xrd.pdf', format='pdf', dpi=1200, bbox_inches='tight')

print('XRD ok for directory:', os.getcwd())
