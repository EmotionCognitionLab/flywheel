#!/usr/bin/env python3
# coding: utf-8

import nibabel as nib
import fw_gear
import shutil

with fw_gear.GearContext() as context:
    nifti = context.config.get_input_path("nifti")
    img = nib.load(nifti)
    shape = img.shape
    nifti_fname = context.config.get_input_filename("nifti")
    shutil.move(nifti, f'/flywheel/v0/output/{nifti_fname}')
    context.metadata.update_file_metadata(
        file_ = nifti_fname,
        container_type = 'acquisition',
        info = {
            'Rows': shape[0],
            'Columns': shape[1],
            'Slices': shape[2] if len(shape) > 2 else 1
        }
    )
