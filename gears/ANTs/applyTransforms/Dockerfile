FROM ubuntu:bionic

ENV ANTSPATH=/usr/lib/ants

# prevent 'gpg: keyserver receive failed: Cannot assign requested address' error
# https://github.com/f-secure-foundry/usbarmory-debian-base_image/issues/9
RUN mkdir -p ~/.gnupg && echo "disable-ipv6" >> ~/.gnupg/dirmngr.conf
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
	       gnupg \
           unzip \
           python3 \
	       wget \
    && wget -O- http://neuro.debian.net/lists/focal.us-ca.full | tee /etc/apt/sources.list.d/neurodebian.sources.list \
    && apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9 \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends ants \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
RUN chmod a+x ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]

