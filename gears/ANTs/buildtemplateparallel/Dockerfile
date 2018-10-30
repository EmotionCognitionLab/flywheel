FROM debian:stretch

ARG DEBIAN_FRONTEND="noninteractive"

ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn \
    ANTSPATH=/usr/lib/ants

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           jq \
           locales \
           gnupg \ 
           unzip \
           python3 \
           python3-pip \
    && curl -sS 'http://neuro.debian.net/_static/neuro.debian.net.asc' | apt-key add - \
    && echo deb http://neurodeb.pirsquared.org data main contrib non-free >> /etc/apt/sources.list.d/neurodebian.sources.list \
    && echo deb http://neurodeb.pirsquared.org stretch main contrib non-free >> /etc/apt/sources.list.d/neurodebian.sources.list \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends ants \
    && pip3 install flywheel-sdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG="en_US.UTF-8" \
    && chmod 777 /opt && chmod a+s /opt

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]

