#!/usr/bin/env python3

"""
Runs the ANTs registration process as a gear.

In some cases the file we want to use as the fixed image
for antsRegistration will be in a zip file. When that
happens, we extract the desired file from the zip, rather than
using the zip file itself as an input.
"""
import json
import logging
import os
from os import path
import shlex
import shutil
import subprocess
import threading
import time

container = '[matherlab/ants-registration]'
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

# set PATH
ANTS_HOME = '/opt/ants-2.5.0/bin'
os.environ['PATH'] = os.environ['PATH'] + ':' + ANTS_HOME

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

def get_reg_command():
    """Builds up the command line arguments for antsRegistration"""
    cmd = [ os.path.join(ANTS_HOME, 'antsRegistration') ]

    fixed_input_file = config['inputs']['fixed']['location']['path']

    moving_input_file = config['inputs']['moving']['location']['path']

    mask_input = config['inputs'].get('mask', None)
    mask_input_file = ''
    if mask_input:
        mask_input_file = mask_input['location']['path']
    
    cmd_line = config['config']['command_line']
    cmd_line = cmd_line.replace('#fixed_input', fixed_input_file)
    cmd_line = cmd_line.replace('#moving_input', moving_input_file)
    cmd_line = cmd_line.replace('#mask_input', mask_input_file)
    cmd.extend(shlex.split(cmd_line))

    return cmd

# def log_resource_utilization(every_n_seconds=300):
#     """Periodically logs resource utilization. Call this in a separate thread; it runs eternally."""
#     while True:
#         total, used, free = shutil.disk_usage(input_dir)
#         logging.debug('disk(used/free/total) GB: %d/%d/%d', used // 2**30, free // 2**30, total // 2**30)
#         logging.debug('vmstat -s -S M output:')
#         subprocess.run(['vmstat', '-s', '-S', 'M'])
#         logging.debug("ps -eo 'cmd,etime,pcpu,pmem' output:")
#         subprocess.run(['ps', '-e', '-o', 'cmd,etime,pcpu,pmem'])
#         time.sleep(every_n_seconds)

# resource_logging_frequency = int(config['config']['log_resource_usage_every_N_seconds'])
# if resource_logging_frequency > 0:
#     usage_logging_thread = threading.Thread(target=log_resource_utilization, kwargs=dict(every_n_seconds=resource_logging_frequency), daemon=True)
#     usage_logging_thread.start()


reg_cmd = get_reg_command()
print('antsRegistration command: ', reg_cmd, flush=True)
try:
    os.chdir(output_dir)
    res = subprocess.run(reg_cmd, check=True, env=os.environ, shell=False, capture_output=True)
    logging.info('Completed successfully')
    logging.info('stdout: %s', res.stdout.decode('utf-8'))
    err_info = res.stderr.decode('utf-8')
    if err_info:
        logging.error('stderr: %s', err_info)
except subprocess.CalledProcessError as err:
    logging.error(f'An error occurred - process exited with code {err.returncode}.')
    logging.info('output: %s', err.output.decode('utf-8'))
    logging.info('stdout: %s', err.stdout.decode('utf-8'))
    logging.error('stderr: %s', err.stderr.decode('utf-8'))
