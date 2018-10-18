#!/usr/bin/env bash
set -e

# Parses config and inputs from flywheel and calls buildtemplateparallel.

CONTAINER="[matherlab/buildtemplateparallel]"
echo -e "$CONTAINER  Initiated"


###############################################################################
# Built to flywheel-v0 spec.

FLYWHEEL_BASE=/flywheel/v0
INPUT_DIR=$FLYWHEEL_BASE/input
OUTPUT_DIR=$FLYWHEEL_BASE/output
MANIFEST=$FLYWHEEL_BASE/manifest.json
CONFIG_FILE=$FLYWHEEL_BASE/config.json

###############################################################################
# Configure the ENV

export USER=Flywheel

###############################################################################
# Map of config parameter names -> buildtemplateparallel command line flags
declare -A param_flags
param_flags[cpu_cores]=-j
param_flags[gradient_step_size]=-g
param_flags[image_dimension]=-d
param_flags[iteration_limit]=-i
param_flags[max_iterations]=-m
param_flags[n4_bias_field_correction]=-n
param_flags[out_prefix]=-o
param_flags[parallel_computation]=-c
param_flags[queue_name]=-q
param_flags[registration_similarity_metric]=-s
param_flags[rigid_body_registration]=-r
param_flags[transformation_model_type]=-t
param_flags[xgrid_args]=-z

##############################################################################
# Parse configuration

function parse_config {

  CONFIG_FILE=$FLYWHEEL_BASE/config.json
  MANIFEST_FILE=$FLYWHEEL_BASE/manifest.json

  if [[ -f $CONFIG_FILE ]]; then
    echo "$(jq -r '.'$1'.'$2 $CONFIG_FILE)"
  else
    echo "$(jq -r '.'$1'.'$2'.default' $MANIFEST_FILE )"
  fi
}

declare -A param_values
for param_name in "${!param_flags[@]}"; do
    param_values[$param_name]="$(parse_config 'config' ${param_name})"
done

input_file="${INPUT_DIR}/$(parse_config 'inputs' 'zip')"
template_file="$(parse_config 'inputs' 'template')"
if [ "${template_file}" != "null" ]; then
    template_file="${INPUT_DIR}/${template_file}"
fi

echo "input file: ${input_file}"
echo "template file: ${template_file}"

##############################################################################
# Unzip the input file
UNZIP_DIR="$INPUT_DIR/unzipped"
$(mkdir -p "$UNZIP_DIR")

# buildtemplateparallel requires all files to be in same folder, so we use -j
# to junk any internal folder structure the zip file may have
unzip -j ${input_file} -d ${UNZIP_DIR}


##############################################################################
# Build up the command line arguments for buildtemplateparallel.sh

btp_cmd="${ANTSPATH}/buildtemplateparallel.sh "

for param_name in "${!param_flags[@]}"; do
    if [ "${param_values[$param_name]}" != "null" ]; then
        btp_cmd="${btp_cmd} ${param_flags[$param_name]} ${param_values[$param_name]}"
    fi
done

if [ "${template_file}" != "null" ]; then
    btp_cmd="${btp_cmd} -z ${template_file}"
fi

input_file_pattern=$(parse_config 'config' 'input_file_pattern')
log_file="btp.log"
btp_cmd="${btp_cmd} ${input_file_pattern} > ${log_file} 2>&1"

echo
echo ${btp_cmd}

##############################################################################
# Run buildtemplateparallel.sh
curdir=$(pwd)
pushd ${curdir}
cd ${UNZIP_DIR}
$btp_cmd
popd

##############################################################################
# Copy results to output directory and write metadata file
out_prefix=${param_values['out_prefix']}
metafile="${OUTPUT_DIR}/.metadata.json"

echo '{ "acquisition" : { "files" : [' > $metafile

if [ -e "${UNZIP_DIR}/${out_prefix}template.nii.gz" ]; then
    echo "{ \"name\": \"${out_prefix}template.nii.gz\" }" >> $metafile
    mv "${UNZIP_DIR}/${out_prefix}template.nii.gz" ${OUTPUT_DIR}
fi

find ${UNZIP_DIR} -name "${out_prefix}${input_file_pattern}" -maxdepth 1 -printf '%f\n' -exec mv {} ${OUTPUT_DIR}/ \; | while read outfname; do
    echo "{ \"name\": \"${outfname}\" }," >> $metafile
done
mv ${UNZIP_DIR}/${log_file} ${OUTPUT_DIR}
echo "{ \"name\": \"${log_file}\" }" >> $metafile
echo '] } }' >> $metafile
