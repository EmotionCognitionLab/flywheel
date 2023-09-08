FROM matherlab/ants-2.5.0

# Install python3
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           python3 \
           python3-pip \
    && pip3 install flywheel-sdk~=14.3.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
RUN chmod a+x ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]

