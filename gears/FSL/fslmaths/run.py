#!/usr/bin/env python3
from flywheel_gear_toolkit import GearToolkitContext
from fsl.wrappers import fslmaths
import logging
log = logging.getLogger(__name__)
import os
import sys

FLYWHEEL='/flywheel/v0'
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
os.environ['FSLDIR'] = '/opt/conda/'
binary_ops = ['add_op', 'sub_op']

def op_to_fn(op, mathobj, context):
    config = context.config
    second_input = context.get_input_path('second_input')
    thr_value = config['thr_value']

    match op:
        case 'add_op':
            log.info(f'adding {second_input} to first input')
            return mathobj.add(second_input)
        case 'bin_op':
            return mathobj.bin()
        case 'bptf_op':
            hp_sigma = config['bptf_hp_sigma']
            lp_sigma = config['bptf_lp_sigma']
            log.info(f'using hp_sigma={hp_sigma}, lp_sigma={lp_sigma}')
            return mathobj.bptf(hp_sigma, lp_sigma)
        case 'sqrt_op':
            return mathobj.sqrt()
        case 'sub_op':
            log.info(f'subtracting {second_input} from first input')
            return mathobj.sub(second_input)
        case 'thr_op':
            log.info(f'using {thr_value} for thr threshold')
            return mathobj.thr(thr_value)
        case 'thrp_op':
            log.info(f'using {thr_value} for thrp threshold')
            return mathobj.thrp(thr_value)
        case 'thrP_op':
            log.info(f'using {thr_value} for thrP threshold')
            return mathobj.thrP(thr_value)
        case other:
            raise ValueError(f'Unknown operation "{op}".')


def run_maths(op, context):
    first_input = context.get_input_path('first_input')
    log.info(f'Running {op} on {first_input}...')
    m = fslmaths(first_input)
    m = op_to_fn(op, m, context)
    output = f'{FLYWHEEL}/output/fslmaths-output.nii.gz'
    m.run(output)
    log.info('Finished running fslmaths.')


def main(context):
    config = context.config
    ops = list(filter(lambda x: x.endswith('_op') and config[x], config.keys()))
    if (len(ops) != 1):
        log.error(f'Expected one operation but found {len(ops)}. Please select one and only one operation to perform.')
        sys.exit(1)

    op = ops[0]

    if(op in binary_ops and not context.get_input_path('second_input')):
        log.error(f'The {op} operation requires a second input and none was provided.')
        sys.exit(2)

    run_maths(op, context)

    
if __name__ == "__main__":
    print('[matherlab/fslmaths] starting...', flush=True)
    with GearToolkitContext(config_path=f"{FLYWHEEL}/config.json") as context:
        context.init_logging()
        main(context)