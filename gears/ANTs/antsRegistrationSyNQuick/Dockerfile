FROM ubuntu:18.04

ENV ANTSPATH=/usr/lib/ants

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

COPY bin/ants /usr/lib/ants

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]

