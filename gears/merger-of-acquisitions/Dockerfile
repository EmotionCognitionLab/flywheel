FROM alpine:3.10

RUN apk update \
    && apk add bash \
    && apk add python3 \
    && apk add py3-pip \
    && pip3 install --upgrade pip \
    && pip3 install flywheel-sdk~=10.1.0

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]