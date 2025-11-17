FROM --platform=linux/amd64 python:3.12-slim-trixie

RUN apt-get update -qq \
    && pip3 install --upgrade pip \
    && pip3 install flywheel-sdk~=21.2.0 \
    && pip3 install fw-gear \
    && pip3 install nibabel


# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
RUN chmod +x ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]