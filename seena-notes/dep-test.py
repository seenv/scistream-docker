try:
    # Python libraries
    import numpy
    import scipy
    import matplotlib
    import h5py
    import zmq
    import tomopy
    import dxchange
    import sewar
    import astropy
    import olefile
    import skimage
    print("All required Python packages are installed.")
    
except ImportError as e:
    print(f"Missing Python package: {e}")
try:
    # System libraries: Check if the libraries are installed using subprocess
    import subprocess

    def check_system_dependency(command, name):
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"{name} is installed.")
        else:
            print(f"{name} is missing or not properly installed.")

    # Check for system-level dependencies
    check_system_dependency("which git", "git")
    check_system_dependency("which swig", "swig")
    check_system_dependency("which flatc", "FlatBuffers compiler (flatc)")
    check_system_dependency("which mpicc", "MPICH (mpicc)")
    check_system_dependency("h5pcc -showconfig | grep 'Parallel HDF5'", "HDF5 with MPI support")

except Exception as e:
    print(f"Error checking system dependencies: {e}")
