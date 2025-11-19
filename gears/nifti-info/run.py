#!/usr/bin/env python3
# coding: utf-8

import nibabel as nib
import fw_gear

with fw_gear.GearContext() as context:
    nifti = context.config.get_input_path("nifti")
    img = nib.load(nifti)
    shape = img.shape
    pixdim = img.header['pixdim']
    acq = context.client.get_acquisition(context.config.destination.get("id"))
    nifti_fname = context.config.get_input_filename("nifti")
    acq.update_file_info(nifti_fname, {
        "Rows": shape[0],
        "Columns": shape[1],
        "Slices": shape[2] if len(shape) > 2 else 1,
        "VoxelX": float(pixdim[1]),
        "VoxelY": float(pixdim[2]),
        "VoxelZ": float(pixdim[3])
    })
