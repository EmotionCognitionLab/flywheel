#!/usr/bin/env python3
# coding: utf-8

import nibabel as nib
import fw_gear

with fw_gear.GearContext() as context:
    nifti = context.config.get_input_path("nifti")
    img = nib.load(nifti)
    shape = img.shape
    context.metadata.update_file_metadata(
        file_ = nifti,
        container_type = 'acquisition',
        info = {
            'Rows': shape[0],
            'Columns': shape[1],
            'Slices': shape[2] if len(shape) > 2 else 1
        }
    )
