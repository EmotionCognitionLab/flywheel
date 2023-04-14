FROM condaforge/miniforge3
ENV PATH="/opt/conda/bin:${PATH}"

# store the FSL public conda channel
ENV FSL_CONDA_CHANNEL="https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public"
# install fsl-avwutils, which is the package that has fslmeants
RUN /opt/conda/bin/conda install -n base -c ${FSL_CONDA_CHANNEL} fsl-avwutils -c conda-forge

ENV FSLDIR="/opt/conda"

# install flywheel
RUN pip install flywheel-gear-toolkit
ENV FLYWHEEL=/flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
RUN chmod +x ${FLYWHEEL}/run

ENTRYPOINT [ "/flywheel/v0/run" ]



