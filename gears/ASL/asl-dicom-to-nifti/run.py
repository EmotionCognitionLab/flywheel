#!/usr/bin/env python3

"""
Given a zip file with 12 dicom images, uses dcm2niix to convert the first
(when dicoms are sorted in ascending alphabetical order by name) image to
a 3D nifti file and the last 10 to a 4D nifti file. (The second is discarded.)
"""

import os
import subprocess
import json
from zipfile import ZipFile

container = '[matherlab/asl-dicom-to-nifti]'
print(container, ' initiated', flush=True)

# key directories/files, as per flywheel spec
flywheel_base = '/flywheel/v0'
input_dir = os.path.join(flywheel_base, 'input')
output_dir = os.path.join(flywheel_base, 'output')
manifest = os.path.join(flywheel_base, 'manifest.json')
config_file = os.path.join(flywheel_base, 'config.json')
input_file_key = 'zip_file'

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

zipfile_path = config['inputs'][input_file_key]['location']['path']
zipfile_name = config['inputs'][input_file_key]['location']['name']
zip = ZipFile(zipfile_path, 'r')
dicom_dir = os.path.join(input_dir, "dicom_files")
os.mkdir(dicom_dir)
zip.extractall(dicom_dir)
zip.close()

dicom_files = os.listdir(dicom_dir)
dicom_files.sort()
if len(dicom_files) != 12:
    print(f"Expected 12 dicom files in {zipfile_name}, but found {len(dicom_files)}. Exiting.")
    raise ValueError

threeD_filename = config['config']['3D_file_name']
fourD_filename = config['config']['4D_file_name']

# call dcm2niix to convert first dicom to 3D nifti
first_dicom = os.path.join(dicom_dir, dicom_files[0])
subprocess.run(['dcm2niix', '-s', 'y', '-z', 'n', '-b', 'n', '-o', output_dir, '-f', threeD_filename, first_dicom], check=True)

# remove the first dicom file (it has been converted to nifti) and second dicom file (not needed)
os.remove(first_dicom)
second_dicom = os.path.join(dicom_dir, dicom_files[1])
os.remove(second_dicom)

# call dcm2niix to convert remaining 10 dicom files to 4D nifti
subprocess.run(['dcm2niix', '-z', 'n', '-b', 'n', '-o', output_dir, '-f', fourD_filename, dicom_dir], check=True)

# write manifest file in output directory
output_files = os.listdir(output_dir)
with open(os.path.join(output_dir, '.manifest.json'), 'w') as manifest:
    json.dump({'acquisition': {'files': [ os.path.join(output_dir, f) for f in output_files ]}}, manifest)

