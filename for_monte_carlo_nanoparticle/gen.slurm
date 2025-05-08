#!/bin/bash

# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=klmc3
#SBATCH --time=0:20:00
#SBATCH --nodes=1

# Replace [budget code] below with your budget code (e.g. t01)
#SBATCH --account=e05-power-sok
#SBATCH --partition=serial
#SBATCH --qos=serial

# Set the number of threads to 1
#   This prevents any threaded system libraries from automatically 
#   using threading.
export OMP_NUM_THREADS=1

# Launch the parallel job
#   Using 512 MPI processes and 128 MPI processes per node
#   srun picks up the distribution from the sbatch options

EXE="/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/bin/KLMC_new/KLMC3/KLMC/klmc"
srun --ntasks-per-node=1 --cpus-per-task=1 --distribution=block:block --hint=nomultithread --exact ${EXE} 1> stdout 2> stderr

# modify
# sed -i "s/0  1  0  1  1/0 1 0 1 1 1/g"  `grep '0  1  0  1  1 ' -rl *.gin`
# sed -i '/output xyz run/d' *.gin
# rm -rf *.out
# rename 's/^X/A/' X*.gin
# python3 0_modify.py
