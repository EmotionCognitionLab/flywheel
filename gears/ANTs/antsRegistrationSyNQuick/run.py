#!/usr/bin/env python3

"""
Runs the ANTs registrationSyNQuick process as a gear.
"""
import json
import os
from os import path
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

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

def get_params():
    """Reads antsRegistrationSyNQuick params from config and associates them with their param flags"""

    # Map of config parameter names -> antsRegistrationSyNQuick command line flags
    param_flags = {}
    param_flags['image_dimension'] = '-d'
    param_flags['out_prefix'] = '-o'
    param_flags['num_threads'] = '-n'
    param_flags['transform_type'] = '-t'
    param_flags['histogram_bin_count'] = '-r'
    param_flags['spline_distance'] = '-s'
    param_flags['precision_type'] = '-p'
    param_flags['use_histogram_matching'] = '-j'

    # Build a map of param flag -> value from the config
    return { param_flags[k]:v for (k, v) in config['config'].items() if k in param_flags }

def get_reg_syn_quick_command():
    """Builds up the command line arguments for antsRegistrationSyNQuick.sh"""
    cmd = [ os.path.join(os.environ['ANTSPATH'], 'antsRegistrationSyNQuick.sh') ]

    fixed_input_file = config['inputs']['fixed']['location']['path']
    cmd.append('-f')
    cmd.append(fixed_input_file)

    moving_input_file = config['inputs']['moving']['location']['path']
    cmd.append('-m')
    cmd.append(moving_input_file)

    mask_file_1 = config['inputs'].get('mask1', None)
    mask_file_2 = config['inputs'].get('mask2', None)
    mask_file_3 = config['inputs'].get('mask3', None)

    if mask_file_1 is not None:
        cmd.append('-x')
        cmd.append(config['inputs']['mask1']['location']['path'])

    if mask_file_2 is not None:
        cmd.append('-x')
        cmd.append(config['inputs']['mask2']['location']['path'])

    if mask_file_2 is None and mask_file_3 is not None:
        cmd.append('-x')
        cmd.append('NULL')

    if mask_file_3 is not None:
        cmd.append('-x')
        cmd.append(config['inputs']['mask3']['location']['path'])

    params = get_params()
    for (param_flag, param_value) in params.items():
        cmd.append(param_flag)
        cmd.append(str(param_value))

    return cmd

rsq_cmd = get_reg_syn_quick_command()
print('antsRegistrationSyNQuick command: ', rsq_cmd, flush=True)
subprocess.run(rsq_cmd, check=True)

out_prefix = config['config']['out_prefix']
expected_files = map(lambda x: out_prefix+x, ['0GenericAffine.mat', '1Warp.nii.gz', '1InverseWarp.nii.gz', 'Warped.nii.gz', 'InverseWarped.nii.gz'])
output_files = []
for f in expected_files:
    if path.exists(f):
        output_path = path.join(output_dir, path.basename(f))
        os.rename(f, output_path)
        output_files.append(output_path)

with open(os.path.join(output_dir, '.manifest.json'), 'w') as manifest:
    json.dump({'acquisition': {'files': output_files }}, manifest)