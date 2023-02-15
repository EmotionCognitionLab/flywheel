FROM --platform=linux/amd64 alpine:3.10

RUN apk update \
    && apk add bash \
    && apk add python3 \
    && apk add py3-pip \
    && apk add gcc \
    && apk add python3-dev \
    && apk add musl-dev \
    && pip3 install --upgrade pip \
    && pip3 install flywheel-sdk~=16.15.9 \
    && pip3 install flywheel-gear-toolkit

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
RUN chmod +x ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]