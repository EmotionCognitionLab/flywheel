FROM condaforge/miniforge3
ENV PATH="/opt/conda/bin:${PATH}"

# store the FSL public conda channel
ENV FSL_CONDA_CHANNEL="https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public"
ENV MATH_ENV="fslmaths-env"
# install fsl-avwutils, which is the package that has fslmaths
RUN conda create -c ${FSL_CONDA_CHANNEL} -c conda-forge -n ${MATH_ENV} fsl-avwutils

# install flywheel
RUN conda run -n ${MATH_ENV} pip install flywheel-sdk flywheel-gear-toolkit
ENV FLYWHEEL=/flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run
COPY run.sh ${FLYWHEEL}/run.sh
RUN chmod +x ${FLYWHEEL}/run.sh

ENTRYPOINT [ "/flywheel/v0/run.sh" ]



