FROM ubuntu:18.04

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
    && wget -q https://github.com/ANTsX/ANTs/archive/v2.3.1.tar.gz \ 
    && gunzip v2.3.1.tar.gz \
    && tar -xf v2.3.1.tar \
    && rm v2.3.1.tar

COPY build-ants.sh /ants/build
RUN chmod +x /ants/build/build-ants.sh
ENTRYPOINT /ants/build/build-ants.sh



