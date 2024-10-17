#!/usr/bin/env python3

"""Runs the ANTs MeasureImageSimilarity process as a gear."""
import json
import os
import subprocess

container = '[matherlab/ants-measureimagesimilarity]'
print(container, 'initiated', flush=True)

# key directories/files, as per flywheel spec
flywheel_base = '/flywheel/v0'
input_dir = os.path.join(flywheel_base, 'input')
os.makedirs(input_dir, exist_ok=True)
output_dir = os.path.join(flywheel_base, 'output')
os.makedirs(output_dir, exist_ok=True)

# set ANTSPATH
os.environ['ANTSPATH'] = '/opt/ants-2.5.0/bin'

# load the config file
config_file = os.path.join(flywheel_base, 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

def input_is_valid():
    """
    Performs some checks for input validity that the manifest can't handle.
    Does not duplicate those that should be handled by the manifest.
    """
    metric = config['config']['metric']
    radius = config['config'].get('radius')
    number_of_bins = config['config'].get('number_of_bins')
    if metric == 'CC' and not radius:
        raise ValueError('The CC metric requires radius to be set.')
    if (metric == 'MI' or metric == 'Mattes') and not number_of_bins:
        raise ValueError(f'The {metric} metric requires number_of_bins to be set.')

    fixed_mask = config['inputs'].get('fixed_image_mask')
    moving_mask = config['inputs'].get('moving_image_mask')
    if moving_mask and not fixed_mask:
        raise ValueError('If you specify a moving mask you must specify a fixed mask as well.')

    return True

def get_command():
    """Builds the shell command that will run MeasureImageSimilarity"""

    cmd = [os.path.join(os.environ['ANTSPATH'], 'MeasureImageSimilarity')]
    cmd.append('--dimensionality')
    cmd.append(str(config['config']['dimensionality']))

    # determine the whole metric string
    fixed_image = config['inputs']['fixed_image']['location']['path']
    moving_image = config['inputs']['moving_image']['location']['path']

    metric = config['config']['metric']
    metric_param = f"{metric}[{fixed_image},{moving_image},{config['config']['metric_weight']},"
    if metric == 'CC':
        metric_param += f"{config['config']['radius']}"
    elif metric == 'MI' or metric == 'Mattes':
        metric_param += f"{config['config']['number_of_bins']}"

    metric_param += f",{config['config']['sampling_strategy']},{config['config']['sampling_percentage']}]"
    cmd.append('--metric')
    cmd.append(metric_param)

    #check for masks
    fixed_mask = config['inputs'].get('fixed_image_mask')
    if fixed_mask:
        cmd.append('--masks')
        moving_mask_path = ''
        moving_mask = config['inputs'].get('moving_image_mask')
        if moving_mask:
            moving_mask_path = moving_mask['location']['path']

        cmd.append(f"[{fixed_mask['location']['path']}, {moving_mask_path}]")

    if config['config'].get('verbose'):
        cmd.append('--verbose')

    if config['config'].get('output_gradient_image'):
        gradient_image_path = os.path.join(output_dir, 'gradient.nii.gz')
        cmd.append('--output')
        cmd.append(gradient_image_path)

    return cmd


input_is_valid()  # raises an error on invalid input
cmd = get_command()
print('MeasureImageSimilarity command: ' + ' '.join(cmd), flush=True)
try:
    res = subprocess.run(cmd, cwd=input_dir, capture_output=True, check=True)
    res_path = os.path.join(output_dir, 'image-similarity-results.txt')
    with open(res_path, 'w') as outfile:
        print(res.stdout.decode('utf-8'), file=outfile)

    if len(res.stderr) > 0:
        print('Errors: ', res.stderr.decode('utf-8'))
    
except subprocess.CalledProcessError as cpe:
    print(f'MeasureImageSimilarity failed. Exit code: {cpe.returncode}')
    print(f"stderr: {cpe.stderr.decode('utf-8')}")
    print(f"stdout: {cpe.stdout.decode('utf-8')}")





