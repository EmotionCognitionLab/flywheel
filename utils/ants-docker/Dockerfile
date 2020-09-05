FROM ubuntu:18.04

# Provides a base image with ANTs v2.3.4 installed from which
# other images that need ANTs can be built.

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    git \
    wget \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /ants/code \
    && mkdir -p /ants/build
RUN cd /ants/code \
    && wget -q https://github.com/ANTsX/ANTs/archive/v2.3.4.tar.gz \ 
    && gunzip v2.3.4.tar.gz \
    && tar -xf v2.3.4.tar \
    && rm v2.3.4.tar \
    && cd /ants/build \
    && cmake /ants/code/ANTs-2.3.4 \
    && make \
    && cd /ants/build/ANTs-build \
    && make install

RUN rm -rf /ants/code \
    && rm -rf /ants/build

RUN apt-get remove build-essential \
    cmake \
    git \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# No entrypoint; this is just meant to provide a base image that has ants-2.3.4



