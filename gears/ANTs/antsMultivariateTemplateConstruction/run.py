#!/usr/bin/env python3

"""
Runs the ANTs multivariateTemplateConstruction process as a gear.

Because antsMultivariateTemplateConstruction takes a variable number of files as inputs,
and because (as of this writing) flywheel can only accept a fixed
number of inputs, the user of the gear should use the Tagger tool
(https://github.com/EmotionCognitionLab/flywheel/tree/master/utils/mark-inputs)
to tag all of the input files and upload a file with the tag info. 
The gear then uses the flywheel sdk to download all of the files
in the tag info file and pass them to antsMultivariateTemplateConstruction. To avoid
collisions between inputs with the same name, the gear prefixes
"subj-" plus the subject label to the file name, e.g. 
't1_32channel.nii.gz' might be downloaded as 
'subj-8081.t1_32channel.nii.gz'. It also uses the sdk to document 
the input files as a note in the 'info' field of the analysis.
"""
import flywheel
import fnmatch
import glob
import re
import json
import logging
import os
from pprint import pprint
import shutil
import subprocess
import threading
import time
from datetime import datetime
from zipfile import ZipFile

container = '[matherlab/antsMultivariateTemplateConstruction]'
print(container, ' initiated', flush=True)

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.DEBUG)

# key directories/files, as per flywheel spec
flywheel_base = '/flywheel/v0'
input_dir = os.path.join(flywheel_base, 'input')
os.makedirs(input_dir, exist_ok=True)
output_dir = os.path.join(flywheel_base, 'output')
os.makedirs(output_dir, exist_ok=True)
manifest = os.path.join(flywheel_base, 'manifest.json')
config_file = os.path.join(flywheel_base, 'config.json')
subject_prefix = 'subj-'

# set ANTSPATH and PATH
os.environ['ANTSPATH'] = '/opt/ants-2.5.0/bin'
os.environ['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/ants-2.5.0/bin'

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

# get the api key from the config
api_key = config['inputs']['api_key']['key']
fw = flywheel.Client(api_key)

def get_params():
    """Reads buildtemplateparallel params from config and associates them with their param flags"""

    # Map of config parameter names -> buildtemplateparallel command line flags
    param_flags = {}
    param_flags['cpu_cores'] = '-j'
    param_flags['num_modalities'] = '-k'
    param_flags['modality_weights'] = '-w'
    param_flags['gradient_step_size'] = '-g'
    param_flags['image_dimension'] = '-d'
    param_flags['iteration_limit'] = '-i'
    param_flags['max_iterations'] = '-m'
    param_flags['save_full_iteration_output'] = '-b'
    param_flags['n4_bias_field_correction'] = '-n'
    param_flags['out_prefix'] = '-o'
    param_flags['parallel_computation'] = '-c'
    param_flags['registration_similarity_metric'] = '-s'
    param_flags['rigid_body_registration'] = '-r'
    param_flags['transformation_model_type'] = '-t'
    param_flags['update_template_with_full_affine'] = '-y'

    # Build a map of btp param flag -> value from the config
    # Exclude params that have empty string values
    params = {}
    for (k, v) in config['config'].items():
        if k in param_flags:
            if isinstance(v, str):
                if (len(v.strip()) > 0):
                    params[param_flags[k]] = v
            else:
                params[param_flags[k]] = v

    return params

def download_input_files(to_dir):
    """Downloads all files under the config['tag'] section of
    the config['tag_file'] file.
    Returns a list of {sessId, parentType="acquisition|analysis", parentId, name} objects.
    """

    tag = config['config']['tag']
    tag_file_info = config['inputs'].get('tag_file', None)
    if tag_file_info == None:
        print("No tag file found. Exiting.")
        raise ValueError

    tag_file = tag_file_info['location']['path']
    with open(tag_file, 'r') as f:
        tag_list = json.load(f)

    results = []
    sess_to_subj = {}
    # we shouldn't have multiple entries with the same tag, but
    # in case we do this will flatten all the resulting 'files' entries
    # into a single result list w/o sublists
    files_to_download = [ item for sublist in [x['files'] for x in tag_list if x['tag'] == tag] for item in sublist ]
    for f in files_to_download:
        sess_id = f['sessId']
        subj_label = sess_to_subj.get(sess_id, None)
        if subj_label == None:
            subj_label = fw.get_session(sess_id).subject.label
            sess_to_subj[sess_id] = subj_label

        results.append(f)
        local_file_name = os.path.join(to_dir, '{0}{1}-{2}-{3}'.format(subject_prefix, subj_label, f['parentId'], f['name']))
        print('Downloading {0} to {1}'.format(f['name'], local_file_name), flush=True)
        if f['parentType'] == 'acquisition':
            fw.download_file_from_acquisition(f['parentId'], f['name'], local_file_name)
        elif f['parentType'] == 'analysis':
            fw.download_output_from_analysis(f['parentId'], f['name'], local_file_name)
        else:
            print('Unknown item parent type "{0}" found. Skipping.'.format(f['parentType']))
    
    return results


def get_command():
    """Builds the shell command that will run antsMultivariateTemplateConstruction"""

    cmd = os.path.join(os.environ['ANTSPATH'], 'antsMultivariateTemplateConstruction.sh')
    params = get_params()
    for (param_flag, param_value) in params.items():
        cmd = cmd + ' ' + param_flag
        if param_value is True:
            cmd = cmd + ' 1'
        elif param_value is False:
            cmd = cmd + ' 0'
        else:
            cmd = cmd + ' ' + str(param_value)

    template_file = config['inputs'].get('template', None)
    if (template_file):
        cmd = cmd + ' -z'
        cmd = cmd + ' ' + template_file['location']['path']
    
    cmd = cmd + ' ' + input_dir + '/' + subject_prefix + '*-' + config['config']['input_file_pattern']

    return cmd


def get_output_files(from_dir):
    """Returns (single_files, files_to_zip) tuple: Each a list of output files to be kept, the first as invidual files, the second in a single zip file.
    This is because Flywheel has a cap on the total number of output files that can be kept.
    Note that not *all* output files are kept.
    """

    out_prefix = config['config']['out_prefix']
    pattern = r'template[0-9]+(.nii.gz|warp.nii.gz|Affine.txt)'
    output_files = [file for file in glob.glob(os.path.join(from_dir, out_prefix + '*')) if re.search(pattern, file) and os.path.isfile(file)]

    zipped_output_files = []
    template_suffixes = ['WarpedToTemplate.nii.gz', 'Repaired.nii.gz']
    for suffix in template_suffixes: 
        output_glob_pattern = os.path.join(from_dir, out_prefix + 'template0' + subject_prefix + '*' + suffix)
        zipped_output_files.extend(glob.glob(output_glob_pattern))

    suffixes = ['Warp.nii.gz', 'Affine.txt']
    for suffix in suffixes:
        output_glob_pattern = os.path.join(from_dir, out_prefix + subject_prefix + '*' + suffix)
        zipped_output_files.extend(glob.glob(output_glob_pattern))

    intermediate_dir = os.path.join(input_dir, 'intermediateTemplates')
    output_glob_pattern = os.path.join(intermediate_dir, '*')
    zipped_output_files.extend(glob.glob(output_glob_pattern))
    
    return (output_files, zipped_output_files)

def save_inputs_to_analysis(input_files):
    """Saves a list of files used as inputs to this analysis as part of the analysis.info field"""

    analysis_id = config['destination']['id']
    # TODO this sets an object with the key 'inputs' into the 'info' field. Figure out how to simply set the 'inputs' field.
    fw.modify_analysis_info(analysis_id, {'set': {'inputs': input_files}})

def log_resource_utilization(every_n_seconds=300):
    """Periodically logs the running procs, disk and CPU utilization. Call this in a separate thread; it runs eternally."""
    while True:
        total, used, free = shutil.disk_usage(input_dir)
        logging.debug('disk(used/free/total) GB: %d/%d/%d', used // 2**30, free // 2**30, total // 2**30)
        logging.debug('vmstat -s -S M output:')
        subprocess.run(['vmstat', '-s', '-S', 'M'])
        logging.debug("ps -eo 'cmd,etime,pcpu,pmem' output:")
        subprocess.run(['ps', '-e', '-o', 'cmd,etime,pcpu,pmem'])
        time.sleep(every_n_seconds)

if (config['config']['log_disk_usage']):
    # DEBUG also log file system setup
    subprocess.run(['df', '-h'])
    # DEBUG also log nproc output
    logging.debug('nproc output:')
    subprocess.run(['nproc'])
    usage_logging_thread = threading.Thread(target=log_resource_utilization, daemon=True)
    usage_logging_thread.start()

input_files = download_input_files(input_dir)
cmd = get_command()
print('cmd: ', cmd, flush=True)
env = os.environ.copy()
env['ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS'] = '8'
subprocess.run(cmd, cwd=input_dir, env=env, check=True, shell=True)

# DEBUG
subprocess.run(['ls', '-lR', '/flywheel/v0/input/'])
(single_output_files, zipped_output_files) = get_output_files(input_dir)
all_output_files = []
# DEBUG
logging.debug('Output files to keep singly: %s', single_output_files)
logging.debug('Output files to zip: %s', zipped_output_files)
# move all of the single output files to the output directory
for f in single_output_files:
    outpath = os.path.join(output_dir, os.path.basename(f))
    os.rename(f, outpath)
    all_output_files.append(outpath)
# zip all of the zipped output files
now = datetime.now()
nowstr = now.strftime('%Y%m%d%H%M%S')
zip_file = os.path.join(output_dir, 'antsMVTC-' + nowstr + '.zip')
with ZipFile(zip_file, 'w') as outzip:
    for f in zipped_output_files:
        outzip.write(f)
# write manifest file in output directory
all_output_files.append(zip_file)
with open(os.path.join(output_dir, '.manifest.json'), 'w') as manifest:
    json.dump({'acquisition': {'files': all_output_files }}, manifest)
save_inputs_to_analysis(input_files)
