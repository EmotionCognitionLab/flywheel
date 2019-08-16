#!/usr/bin/env python3

"""
Runs the ANTs buildtemplateparallel process as a gear.

Because buildtemplateparallel takes a variable number of files as inputs,
and because (as of this writing) flywheel can only accept a fixed
number of inputs, the user of the gear should use the Tagger tool
(https://github.com/EmotionCognitionLab/flywheel/tree/master/utils/mark-inputs)
to tag all of the input files and upload a file with the tag info. 
The gear then uses the flywheel sdk to download all of the files
in the tag info file and pass them to buildtemplateparallel. To avoid
collisions between inputs with the same name, the gear prefixes
"subj-" plus the subject label to the file name, e.g. 
't1_32channel.nii.gz' might be downloaded as 
'subj-8081.t1_32channel.nii.gz'. It also uses the sdk to document 
the input files as a note in the 'info' field of the analysis.
"""
import flywheel
import fnmatch
import glob
import json
import os
from pprint import pprint
import subprocess

container = '[matherlab/buildtemplateparallel]'
print(container, ' initiated', flush=True)

# key directories/files, as per flywheel spec
flywheel_base = '/flywheel/v0'
input_dir = os.path.join(flywheel_base, 'input')
os.makedirs(input_dir, exist_ok=True)
output_dir = os.path.join(flywheel_base, 'output')
os.makedirs(output_dir, exist_ok=True)
manifest = os.path.join(flywheel_base, 'manifest.json')
config_file = os.path.join(flywheel_base, 'config.json')
subject_prefix = 'subj-'

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

# get the api key from the config
api_key = config['inputs']['api_key']['key']
fw = flywheel.Flywheel(api_key)

def get_btp_params():
    """Reads buildtemplateparallel params from config and associates them with their param flags"""

    # Map of config parameter names -> buildtemplateparallel command line flags
    param_flags = {}
    param_flags['cpu_cores'] = '-j'
    param_flags['gradient_step_size'] = '-g'
    param_flags['image_dimension'] = '-d'
    param_flags['iteration_limit'] = '-i'
    param_flags['max_iterations'] = '-m'
    param_flags['n4_bias_field_correction'] = '-n'
    param_flags['out_prefix'] = '-o'
    param_flags['parallel_computation'] = '-c'
    param_flags['queue_name'] = '-q'
    param_flags['registration_similarity_metric'] = '-s'
    param_flags['rigid_body_registration'] = '-r'
    param_flags['transformation_model_type'] = '-t'
    param_flags['xgrid_args'] = '-z'

    # Build a map of btp param flag -> value from the config
    return { param_flags[k]:v for (k, v) in config['config'].items() if k in param_flags }

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
        local_file_name = os.path.join(to_dir, '{0}{1}-{2}'.format(subject_prefix, subj_label, f['name']))
        print('Downloading {0} to {1}'.format(f['name'], local_file_name), flush=True)
        if f['parentType'] == 'acquisition':
            fw.download_file_from_acquisition(f['parentId'], f['name'], local_file_name)
        elif f['parentType'] == 'analysis':
            fw.download_output_from_analysis(f['parentId'], f['name'], local_file_name)
        else:
            print('Unknown item parent type "{0}" found. Skipping.'.format(f['parentType']))
    
    return results


def get_btp_command():
    """Builds the shell command that will run buildtemplateparallel"""

    btp_cmd = [ os.path.join(os.environ['ANTSPATH'], 'buildtemplateparallel.sh') ]
    params = get_btp_params()
    for (param_flag, param_value) in params.items():
        btp_cmd.append(param_flag)
        btp_cmd.append(str(param_value))

    template_file = config['inputs'].get('template', None)
    if (template_file):
        btp_cmd.append('-z')
        btp_cmd.append(template_file['location']['path'])
    
    btp_cmd.append(subject_prefix + '*-' + config['config']['input_file_pattern'])

    return btp_cmd


def get_output_files(from_dir):
    """Returns list of files we want to keep from the output generated by buildtemplateparallel.
    Note that not *all* output files are kept.
    """

    output_files = []
    out_prefix = config['config']['out_prefix']
    output_template = os.path.join(from_dir, out_prefix + 'template.nii.gz')
    if (os.path.isfile(output_template)):
        output_files.append(output_template)

    input_file_pattern = config['config']['input_file_pattern']
    output_glob_pattern = os.path.join(from_dir, out_prefix + subject_prefix + '*-' + input_file_pattern)
    output_files.extend(glob.glob(output_glob_pattern))

    
    return output_files

def save_inputs_to_analysis(input_files):
    """Saves a list of files used as inputs to this analysis as part of the analysis.info field"""

    analysis_id = config['destination']['id']
    # TODO this sets an object with the key 'inputs' into the 'info' field. Figure out how to simply set the 'inputs' field.
    fw.modify_analysis_info(analysis_id, {'set': {'inputs': input_files}})


input_files = download_input_files(input_dir)
btp_cmd = get_btp_command()
print('btp_cmd: ' + ' '.join(btp_cmd), flush=True)
subprocess.run(btp_cmd, cwd=input_dir, check=True)
output_files = get_output_files(input_dir)
# move all of the output files to the output directory
for f in output_files:
    os.rename(f, os.path.join(output_dir, os.path.basename(f)))
# write manifest file in output directory
with open(os.path.join(output_dir, '.manifest.json'), 'w') as manifest:
    json.dump({'acquisition': {'files': [ os.path.join(output_dir, os.path.basename(f)) for f in output_files ]}}, manifest)
save_inputs_to_analysis(input_files)
