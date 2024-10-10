#!/usr/bin/env python3

"""Runs the ANTs applyTransform process as a gear."""
import json
import os
import subprocess
from zipfile import ZipFile

container = '[matherlab/ants-applytransform]'
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
    """Reads applyTransform params from config and associates them with their param flags"""

    # Map of config parameter names -> antsApplyTransform command line flags
    param_flags = {}
    param_flags['dimensionality'] = '-d'
    param_flags['input_image_type'] = '-e'
    param_flags['interpolation'] = '-n'
    param_flags['verbose'] = '-v'
    param_flags['float'] = '--float'

    # Build a map of applyTransform param flag -> value from the config
    params = { param_flags[k]:v for (k, v) in config['config'].items() if k in param_flags }
    for x in ['-v', '--float']: # convert True to 1/False to 0
        if params.get(x, False):
            params[x] = 1
        if not params.get(x, True):
            params[x] = 0

    return params

def get_inputs():
    """
    Returns the various *non-transform* input files with their respective param flags
    as well as the output file name.
    """
    input_file = config['inputs']['input_file']['location']['path']
    reference_file = config['inputs']['reference_file']['location']['path']
    input_file_name_parts = os.path.basename(input_file).split('.')
    if len(input_file_name_parts) >= 2:
        input_file_name_parts.pop() # assume final item is file extension
        if input_file_name_parts[len(input_file_name_parts) - 1] == 'nii':
            input_file_name_parts.pop()
    output_file_name = '.'.join(input_file_name_parts) + '_warped.nii.gz'
    output_file_path = os.path.join(output_dir, output_file_name)

    return { '-i': input_file, '-r': reference_file, '-o': output_file_path }

def get_transforms():
    """
    There can be between 2 and 9 transforms. (These limits are imposed by the gear, not
    by antsApplyTransform.) Each transform file may either be an ordinary gear input or
    may be a file inside a zip input. One zip input may (in fact, is likely) to contain
    more than one transform file.
    All of this means that there is one mandatory and eight optional inputs for the gear
    and nine optional paramaters corresponding to those inputs. In the simplest case,
    there are two ordinary (non-zip) files specified as inputs and these are passed to
    antsApplyTransform. A more complicated case might look something like this:
    Inputs:
      transform_file_1: some_zip
      transform_file_2: <blank>
      transform_file_3: some_non_zip
      transform_file_4: some_non_zip
    Params:
      transform_target_1: name of file to extract from transform_file_1 zip file
      transform_target_2: name of file to extract. Because transform_file_2 is blank, we assume
        it is to be extracted from the transform_file_1 zip file.
      transform_target_3 through 9: <blank>

    The transform_target_1 through 9 params are used solely to specify which files should be
    extracted from any zip files specified. If no zip file is specified for a given transform_target
    param, the last zip file specified should be used.

    Additionally, each of the nine transforms can have an optional inverse flag associated with
    it, specifying that the inverse of the specified transform should be applied.
    """
    transform_files = [ config['inputs'].get('transform_file_' + str(x), None) for x in range(1,10) ]
    transform_targets = [ config['config'].get('transform_target_' + str(x), None) for x in range(1, 10) ]
    transform_inversions = [ config['config'].get('invert_transform_' + str(x), None) for x in range(1, 10)]

    transforms = []
    cur_zip = None
    for (target, file, inversion) in zip(transform_targets, transform_files, transform_inversions):
        if file is None:
            if target is None:
                if inversion:
                    # error - no transform file/target was given, but they want to invert this non-existent transform
                    raise ValueError('Found transform inversion, but no associated transform.')
                continue
            if cur_zip is None:
                # error - a target has been specified, but we haven't yet seen a 
                # zip file to extract anything from
                raise ValueError('Found transform target {} , but no zip file to extract it from'.format(target))
        elif file['location']['path'].endswith('zip'):
            cur_zip = file['location']['path']
        else:
            # just a regular file; append it to transforms
            transforms.append('-t')
            if inversion:
                transforms.append(f"[{file['location']['path']}, 1]")
            else:
                transforms.append(file['location']['path'])
        if target is not None:
            with ZipFile(cur_zip) as zipfile:
                zipfile.extract(target, os.path.dirname(cur_zip))
            transforms.append('-t')
            if inversion:
                transforms.append(f"[{os.path.join(os.path.dirname(cur_zip), target)}, 1]")
            else:
                transforms.append(os.path.join(os.path.dirname(cur_zip), target))
        # if target is None it's weird, but not illegal - the zip file may be referred to by a later target

    if len(transforms) < 4: # we need a minimum of two transforms, each preceded by '-t'
        raise ValueError('Too few transforms provided - a minimum of two is required.')
    if len(transforms) % 2:
        raise ValueError('Error generating transforms; odd number of arguments: {}.'.format(transforms))
    if len(transforms) > 18: # max of nine transforms allowed, each preceded by '-t'
        raise ValueError('Too many transforms provided - a maximum of nine is allowed.')

    return transforms

def get_command():
    """Builds the shell command that will run antsApplyTransforms"""

    cmd = [ os.path.join(os.environ['ANTSPATH'], 'antsApplyTransforms') ]
    params = get_params()
    for (param_flag, param_value) in params.items():
        cmd.append(param_flag)
        cmd.append(str(param_value))
    inputs = get_inputs()
    for (input_flag, input_value) in inputs.items():
        cmd.append(input_flag)
        cmd.append(str(input_value))
    cmd.extend(get_transforms())

    return cmd

cmd = get_command()
print('antsApplyTransforms command: ' + ' '.join(cmd), flush=True)
subprocess.run(cmd, cwd=input_dir, check=True)

# write manifest file in output directory
all_output_files = os.listdir(output_dir) # shouldn't be any subdirectories
with open(os.path.join(output_dir, '.manifest.json'), 'w') as manifest:
    json.dump({'acquisition': {'files': all_output_files }}, manifest)
