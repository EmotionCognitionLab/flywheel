#!/usr/bin/env python3
from flywheel_gear_toolkit import GearToolkitContext
import logging
log = logging.getLogger(__name__)
import os
import subprocess
import tempfile

FLYWHEEL='/flywheel/v0'
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
os.environ['FSLDIR'] = '/opt/conda/'

def valid_coordinate(coord_str):
    coords = coord_str.split()
    if (len(coords) != 3):
        return False
    
    return all(map(lambda x: x.isnumeric(), coords))
        

def build_cmd(context):
    cmd = [f'{os.environ["FSLDIR"]}bin/fslmeants', '-i', context.get_input_path("input")]
    config = context.config
    
    if config['coordinate'] and len(config['coordinate']) > 0:
       coord = config['coordinate']
       if not valid_coordinate(coord):
           raise ValueError(f'Expected coordinate to be three numbers separated by spaces, but got "{coord}".')
       
       log.info('Coordinates provided, not using mask')
       cmd.append('-c')
       cmd.append(coord)
       if config['use_mm']:
           cmd.append('--usemm')
    elif context.get_input_path('mask_file'):
        cmd.append('-m')
        cmd.append(context.get_input_path('mask_file'))

    if config['eig']:
        cmd.append('--eig')
        if config['no_bin']:
            cmd.append('--no-bin')
        if config['order']: # TODO is there any way that 0 is a legitimate order value?
            cmd.append('--order')
            cmd.append(str(config['order']))

    if config['show_all']:
        cmd.append('--showall')

    if config['transpose']:
        cmd.append('--transpose')

    if config['verbose']:
        cmd.append('--verbose')

    if config['weighted']:
        cmd.append('--weighted')
        
    (output_handle, output_name) = tempfile.mkstemp(prefix='fslmeants-output-', suffix='.txt', dir=f'{FLYWHEEL}/output/')
    os.close(output_handle) # we just need the name; close it and let fslmeants write to it
    cmd.append('-o')
    cmd.append(output_name)
    
    return cmd


def run_meants(context):
    cmd = build_cmd(context)
    log.info(f'Running command: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    log.info(result.stdout)
    if len(result.stderr) > 0:
        log.error(result.stderr)
    result.check_returncode()
    log.info('Finished running fslmeants.')


def main(context):
    run_meants(context)

    
if __name__ == "__main__":
    print('[matherlab/fslmeants] starting...', flush=True)
    with GearToolkitContext(config_path=f"{FLYWHEEL}/config.json") as context:
        context.init_logging()
        main(context)