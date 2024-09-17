FROM continuumio/miniconda3 as base

RUN apt-get update --fix-missing && apt-get install -y \
    build-essential \
    libzmq3-dev \
    swig \
    git \
#    libmpich-dev \         #doesn't work if you have already mpi on your system
#    libhdf5-mpich-dev \    # do best is to install it inside the env and use that
    apt-utils \
    net-tools \
    iptables \
    iputils-ping \
    iproute2 \
    nano
RUN conda install -y \
    python=3.11 \
    numpy \
    scipy \
    matplotlib \
    pyzmq \
    pip \
    cmake
RUN conda install -c conda-forge hdf5=1.14.3=mpi* mpich  # so you are sure that is has parallel activated
RUN conda install -c conda-forge compilers            # because the Conda-installed MPICH compiler needs its compiler
RUN pip install astropy olefile             # some versions don't install it automatically

RUN pip install --upgrade pip

RUN git clone https://github.com/google/flatbuffers.git
WORKDIR /flatbuffers
RUN cmake -G "Unix Makefiles"
RUN make -j
RUN make install

WORKDIR /
RUN git clone https://github.com/diaspora-project/aps-mini-apps.git
WORKDIR /aps-mini-apps
RUN git fetch origin
RUN git checkout master

RUN mkdir build
RUN mkdir build/python
RUN mkdir build/python/quality

# Setup quality checker
RUN pip install sewar
RUN cp ./python/quality/iqcheck.py ./build/python/quality

# Setup flatbuffers data structures
WORKDIR /aps-mini-apps/include/tracelib
RUN flatc -c trace_prot.fbs     # ignore the "lower case" warning
WORKDIR /aps-mini-apps

# Build SIRT
FROM base as streamersirt
WORKDIR /aps-mini-apps/build
#RUN cmake ..
RUN export MPICC=$(which mpicc)
RUN export MPICXX=$(which mpicxx)
RUN echo $MPICC
RUN echo $MPICXX
RUN cmake -DCMAKE_C_COMPILER=$(which mpicc) -DCMAKE_CXX_COMPILER=$(which mpicxx) ..
RUN make
WORKDIR /aps-mini-apps/build/bin

# Build streamer-dist
FROM streamersirt as dist
RUN conda install -y -c conda-forge \
    tomopy \
    dxchange
WORKDIR /aps-mini-apps/build/python
#RUN mkdir streamer-dist
RUN cp ../../python/streamer-dist/ModDistStreamPubDemo.py ./streamer-dist
RUN cp -r ../../python/common ./
WORKDIR /aps-mini-apps/build/python/streamer-dist

EXPOSE 50010
