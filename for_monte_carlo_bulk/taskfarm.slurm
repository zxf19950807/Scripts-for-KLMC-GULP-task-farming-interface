#!/bin/bash

# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=KLMC
#SBATCH --time=24:00:00
#SBATCH --nodes=32

# Replace [budget code] below with your budget code (e.g. t01)
#SBATCH --account=e05-power-sok
#SBATCH --partition=standard
#SBATCH --qos=standard

# Set the number of threads to 1
#   This prevents any threaded system libraries from automatically 
#   using threading.
export OMP_NUM_THREADS=1
export SLURM_CPU_FREQ_REQ=2250000

# Launch the parallel job
#   Using 512 MPI processes and 128 MPI processes per node
#   srun picks up the distribution from the sbatch options

srun --ntasks-per-node=128 --cpus-per-task=1 --distribution=block:block --hint=nomultithread --exact /mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/bin/KLMC/KLMC3/build/tf.x 1> stdout 2> stderr
