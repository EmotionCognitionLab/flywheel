#!/usr/bin/env python3

"""
Runs the ANTs ResampleImage process as a gear.
"""
import json
import os
from os import path
import subprocess
import sys

container = '[matherlab/ants-resampleimage]'
print(container, ' initiated', flush=True)

# key directories/files, as per flywheel spec
flywheel_base = '/flywheel/v0'
input_dir = os.path.join(flywheel_base, 'input')
os.makedirs(input_dir, exist_ok=True)
output_dir = os.path.join(flywheel_base, 'output')
os.makedirs(output_dir, exist_ok=True)
manifest = os.path.join(flywheel_base, 'manifest.json')
config_file = os.path.join(flywheel_base, 'config.json')

# set ANTSPATH
os.environ['ANTSPATH'] = '/opt/ants-2.5.0/bin'

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

def get_resample_image_command():
    """Builds up the command line arguments for ResampleImage"""
    cmd = [ os.path.join(os.environ['ANTSPATH'], 'ResampleImage') ]

    cmd.append(str(config['config']['image_dimension']))

    input_file = config['inputs']['inputImage']['location']['path']
    cmd.append(input_file)

    outfile_name = config['config']['output_image']
    final_output_path = path.join(output_dir, outfile_name)
    cmd.append(final_output_path)

    cmd.append(config['config']['MxNxO'])
    size_or_spacing = config['config']['size_or_spacing']
    if size_or_spacing:
        cmd.append('1')
    else:
        cmd.append('0')

    if config['config'].get('interpolation_type', None):
        cmd.append(config['config']['interpolation_type'])
    if config['config'].get('pixel_type', None):
        cmd.append(str(config['config']['pixel_type']))
    
    return cmd


rsi_cmd = get_resample_image_command()
print('ResampleImage command: ', rsi_cmd, flush=True)
subprocess.run(rsi_cmd, check=True, env=os.environ)

outfile_name = config['config']['output_image']
final_output_path = path.join(output_dir, outfile_name)

if path.exists(final_output_path):
    os.rename(final_output_path, final_output_path)
else:
    print('Expected output file %s was not found. Check log for errors.' % final_output_path)
    sys.exit(1)

with open(os.path.join(output_dir, '.manifest.json'), 'w') as manifest:
    json.dump({'acquisition': {'files': [ final_output_path ] }}, manifest)