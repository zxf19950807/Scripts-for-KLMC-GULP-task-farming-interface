#!/bin/bash

# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=np
#SBATCH --time=96:00:00
#SBATCH --nodes=64

# Replace [budget code] below with your budget code (e.g. t01)
#SBATCH --account=e05-power-sok
#SBATCH --partition=standard
#SBATCH --qos=long

# Set the number of threads to 1
#   This prevents any threaded system libraries from automatically 
#   using threading.
export OMP_NUM_THREADS=1

# SCOREP ENV
module unload perftools-base/22.12.0
module load other-software
module load PrgEnv-gnu
module load scalasca/2.6.1-gcc11
export SCOREP_MEMORY_RECORDING=true
SLURM_CPU_FREQ_REQ=2250000
# Launch the parallel job
#   Using 512 MPI processes and 128 MPI processes per node
#   srun picks up the distribution from the sbatch options

#/work/ta159/ta159/ta159wkjee/Software/checkmem/check_mem.sh 1> check_mem.out 2> check_mem.err &
#sleep 30

EXE="/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/bin/KLMC_new/KLMC3/_build/klmc3.062024.x"
srun --ntasks-per-node=128 --cpus-per-task=1 --distribution=block:block --hint=nomultithread --exact ${EXE} 1> stdout 2> stderr

