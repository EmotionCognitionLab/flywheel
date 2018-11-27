# Create a base docker container that will run Multi-echo ICA

FROM neurodebian:xenial
MAINTAINER Mather Lab

# Install dependencies
RUN apt-get update \
    && apt-get install -y \
        python2.7 \
        python-pip \
        afni \
        numpy \
        scipy
#ADD https://github.com/ME-ICA/me-ica.git
RUN git clone https://github.com/ME-ICA/me-ica.git

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json
COPY meica_ns2.py ${FLYWHEEL}/meica_ns2.py

# Configure entrypoint for the run script
ENTRYPOINT ["/flywheel/v0/run"]
