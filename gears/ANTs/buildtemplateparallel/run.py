#!/usr/bin/env python3

"""
Runs the ANTs buildtemplateparallel process as a gear.

Because buildtemplateparallel takes multiple files as input,
and because (as of this writing) flywheel can only accept one
input file, the user of the gear should build a collection of
files in the flywheel GUI and select one of them as input. 
The gear then uses the flywheel sdk to download all of the files
in the collection and pass them to buildtemplateparallel. To avoid
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
output_dir = os.path.join(flywheel_base, 'output')
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
    """Downloads all nifti files that (a) have a name matching config['input_file_pattern']
    and (b) are in acquisitions that are in sessions tagged with config['tag'].
    Returns a list of {session_id, file_id, file_name} objects.
    """

    project_label = config['config']['project']
    project = fw.projects.find_first('label='+project_label)
    if project == None:
        print("No project named {} found. Exiting.".format(project_label))
        raise ValueError
    tag = config['config']['tag']
    sessions = project.sessions.find('tags='+tag)
    if len(sessions) == 0:
        print("No sessions with the tag {} found in project {}. Exiting.".format(tag, project_label))
        raise ValueError

    results = []
    for s in sessions:
        subject = s.subject
        subj_label = subject_prefix + subject.label + '-'
        acquisitions = s.acquisitions()
        for a in acquisitions:
            files = [ f for f in a.files if f.type == 'nifti' and fnmatch.fnmatch(f.name, config['config']['input_file_pattern']) ]
            for f in files:
                results.append({'acquisition_id': a.id, 'file_id': f.id, 'file_name': f.name})
                local_file_name = os.path.join(to_dir, subj_label + f.name)
                print('Downloading {0} to {1}'.format(f.name, local_file_name), flush=True)
                fw.download_file_from_acquisition(a.id, f.name, local_file_name)
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
