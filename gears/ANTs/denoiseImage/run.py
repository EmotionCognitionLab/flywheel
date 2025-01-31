#!/usr/bin/env python3

"""Runs the ANTs denoiseImage process as a gear."""
import json
import os
import subprocess

container = '[matherlab/ants-denoiseimage]'
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
    """Reads denoiseImage params from config and associates them with their param flags"""

    # Map of config parameter names -> denoiseImage command line flags
    param_flags = {}
    param_flags['dimensionality'] = '--image-dimensionality'
    param_flags['shrink_factor'] = '--shrink-factor'
    param_flags['noise_model'] = '--noise-model'
    param_flags['verbose'] = '--verbose'
    param_flags['patch_radius'] = '--patch-radius'
    param_flags['search_radius'] = '--search-radius'

    # Build a map of denoiseImage param flag -> value from the config
    params = { param_flags[k]:v for (k, v) in config['config'].items() if k in param_flags }
    if params.get('--verbose', False):
        params['--verbose'] = 1
    if not params.get('--verbose', True):
        params['--verbose'] = 0

    return params

def get_ouputs():
    """
    Returns the outpout parameter (including the optional estimated noise image, if requested).
    Adds output directory to provide file name(s).
    """
    output_file_path = os.path.join(output_dir, config['config']['output_image'])
    noise_image_file = config['config'].get('noise_image', None)
    if noise_image_file:
        noise_file_path = os.path.join(output_dir, noise_image_file)
        return { '--output': f'[ {output_file_path}, {noise_file_path} ]' }
    
    return { '--output': output_file_path }

def get_inputs():
    """
    Returns the main input image argument and the arg for the mask image (if specified).
    """
    input_file = config['inputs']['input_file']['location']['path']
    mask_image = config['inputs'].get('mask_image', None)
    mask_image_file = None
    if (mask_image):
        mask_image_file = mask_image['location']['path']
        return { '--input-image': input_file, '--mask-image': mask_image_file }
    
    return { '--input-image': input_file }

def get_command():
    """Builds the shell command that will run denoiseImage"""

    cmd = [ os.path.join(os.environ['ANTSPATH'], 'DenoiseImage') ]
    params = get_params()
    for (param_flag, param_value) in params.items():
        cmd.append(param_flag)
        cmd.append(str(param_value))
    inputs = get_inputs()
    for (input_flag, input_value) in inputs.items():
        cmd.append(input_flag)
        cmd.append(str(input_value))
    outputs = get_ouputs()
    for (output_flag, output_value) in outputs.items():
        cmd.append(output_flag)
        cmd.append(str(output_value))

    return cmd

cmd = get_command()
print('denoiseImage command: ' + ' '.join(cmd), flush=True)
subprocess.run(cmd, cwd=input_dir, check=True)

