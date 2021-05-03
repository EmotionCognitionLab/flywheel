FROM poldracklab/mriqc:0.15.1

# Install flywheel sdk
RUN pip install flywheel-sdk~=14.6.2

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
RUN chmod a+x ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

ENTRYPOINT ["/flywheel/v0/run"]

