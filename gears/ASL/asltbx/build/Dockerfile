FROM ubuntu:xenial
LABEL maintainer "Noah Mercer"

RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    gnupg \
    libxi6 \
    libxt6 \
    libxtst6 \
    unzip \
    wget \
    # matlab installer just says "finished" w/o doing anything unless some X app is installed...
    xterm \
    --no-install-recommends && \
    cd /opt && \
    echo "Downloading SPM..." && \
    wget -q http://www.fil.ion.ucl.ac.uk/spm/download/restricted/eldorado/spm12.zip && \
    echo "Unzipping SPM..." && \
    unzip -q spm12.zip && \
    rm spm12.zip && \
    echo "Downloading flywheel sdk..." && \
    wget -q https://github.com/flywheel-io/core/releases/download/10.0.1/flywheel-matlab-sdk-10.0.1.zip && \
    echo "Unzipping flywheel sdk..." && \
    unzip -q flywheel-matlab-sdk-10.0.1.zip && \
    rm flywheel-matlab-sdk-10.0.1.zip && \
    rm -rf /var/lib/apt/lists/*

# Prep matlab installer
RUN mkdir /matlab-installer
COPY matlab_R2018b_glnxa64.zip /matlab-installer
RUN cd /matlab-installer && unzip -q matlab_R2018b_glnxa64.zip && rm matlab_R2018b_glnxa64.zip

CMD /bin/bash