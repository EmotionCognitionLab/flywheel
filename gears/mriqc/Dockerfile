FROM poldracklab/mriqc:0.15.1

# Install flywheel sdk
RUN pip install flywheel-sdk~=14.6.2

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.sh ${FLYWHEEL}/run
RUN chmod a+x ${FLYWHEEL}/run
COPY run.py ${FLYWHEEL}/run.py
COPY manifest.json ${FLYWHEEL}/manifest.json
# ENV preservation for Flywheel Engine
RUN env -u HOSTNAME -u PWD | \
  awk -F = '{ print "export " $1 "=\"" $2 "\"" }' > ${FLYWHEEL}/docker-env.sh

ENTRYPOINT ["/flywheel/v0/run"]

