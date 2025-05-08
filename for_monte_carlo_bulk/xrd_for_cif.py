"""
Dans_Diffraction Examples
Generate powder spectrum from a cif file
"""
import sys, os
import numpy as np
import matplotlib.pyplot as plt  # Plotting
from matplotlib import rcParams
import matplotlib
cf = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(cf, '..'))
import Dans_Diffraction as dif
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
                               
matplotlib.rcParams.update({'font.size': 6, 'font.family': 'DejaVu Sans'})
plt.rcParams['axes.linewidth'] = 0.2
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['ytick.minor.width'] = 0.2
plt.rcParams['ytick.major.width'] = 0.2
plt.rcParams['xtick.minor.width'] = 0.2
plt.rcParams['xtick.major.width'] = 0.2
plt.rcParams['axes.linewidth'] = 0.2

cm = 1/2.54
fig, ax = plt.subplots(figsize=(8*cm, 4*cm))

# import cif
if os.path.exists('b.cif'):
    f = 'b.cif'
elif os.path.exists('a.cif'):
    f = 'a.cif'
elif os.path.exists('1.cif'):
    f = '1.cif'
else:
    print("cannot find cif")

xtl = dif.Crystal(f)

energy_kev = dif.fc.wave2energy(1.5498)  # 8 keV
max_twotheta = 120

# xtl.Scatter.setup_scatter('xray')  # 'xray','neutron','xray magnetic','neutron magnetic','xray resonant'
# max_wavevector = dif.fc.calqmag(max_twotheta, energy_kev)
# q, intensity = xtl.Scatter.generate_powder(max_wavevector, peak_width=0.01, background=0, powder_average=True)
q, intensity, reflections = xtl.Scatter.powder('xray', units='Q', energy_kev=energy_kev, peak_width=0.01, background=0)

# convert wavevector, q=2pi/d to two-theta:
twotheta = dif.fc.cal2theta(q, energy_kev)

# save data as csv file
head = '%s\nx-ray powder diffraction energy=%6.3f keV\n two-theta, intensity' % (xtl.name, energy_kev)
np.savetxt('powder.csv', (twotheta, intensity), delimiter=',', header=head)

# plot the spectra
ax.plot(twotheta, intensity, '-', lw=0.6, color='#304697')
# dif.fp.labels('x-ray powder diffraction E=%6.3f keV\n%s' % (energy_kev, xtl.name), 'two-theta', 'intensity')

ax.set_xlabel("2θ (degrees)", fontsize=7)
ax.set_ylabel("Intensity", fontsize=7)
ax.set_xlim(0, 120)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_locator(MultipleLocator(20))
ax.xaxis.set_minor_locator(MultipleLocator(5))

fig.savefig('xrd.png', dpi=1200, bbox_inches='tight')
fig.savefig('xrd.pdf', format='pdf', dpi=1200, bbox_inches='tight')

print('XRD ok')