
# Start with Matlab R2018b runtime
FROM flywheel/matlab-mcr:v95

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}

# copy the Matlab Stand-Alone (MSA) into the container.
COPY bin/asltbx_gear ${FLYWHEEL}/run

# Ensure that the standalone and its run script are executable
RUN chmod +x ${FLYWHEEL}/run

# Copy manifest
COPY manifest.json ${FLYWHEEL}/manifest.json

# Configure entrypoint
ENTRYPOINT ["/flywheel/v0/run"]