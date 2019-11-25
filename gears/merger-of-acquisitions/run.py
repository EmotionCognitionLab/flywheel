#!/usr/bin/env python3
# coding: utf-8

import flywheel
import json
import os
import re
import sys
import tempfile
import zipfile

container = '[matherlab/merger-of-acquisitions]'
print(container, ' initiated', flush=True)

# key directories/files, as per flywheel spec
flywheel_base = '/flywheel/v0'
manifest = os.path.join(flywheel_base, 'manifest.json')
config_file = os.path.join(flywheel_base, 'config.json')

# load the config file
with open(config_file, 'r') as f:
    config = json.load(f)

api_key = config['inputs']['api_key']['key']
fw = flywheel.Flywheel(api_key)

session_id = config['config']['session_id']
all_sessions = config['config']['all_sessions']
if not all_sessions and session_id == '':
    print('You must either provide a session id or process all sessions. Exiting.', flush=True)
    sys.exit(1)

acq_merge_prefixes = list(map(lambda i: i.strip(), config['config']['acquisition_prefixes'].split(',')))
if len(acq_merge_prefixes) == 0:
    print('You must provide at least one acquisition prefix. Exiting.', flush=True)
    sys.exit(1)
acq_merge_patterns = list(map(lambda x: re.compile(x + '[123]'), acq_merge_prefixes))

dest_session_id = config['destination']['id']
dest_session = fw.get_session(dest_session_id)
project = fw.get_project(dest_session.project)

def get_acquisitions_to_merge(acq_pattern, acquisitions, expected_count=3):
    result = list(filter(lambda acq: acq_pattern.fullmatch(acq.label), acquisitions))
    if len(result) > 0:
        assert len(result) == expected_count
    
    return result

def merge_acquisitions(acquisitions, new_acquisition_label, session):
    if len(acquisitions) == 0:
        return
    labels = ', '.join(list(map(lambda acq: acq.label, acquisitions)))
    print(f'Merging {labels} to {new_acquisition_label} for {session.subject.label}/{session.label}.', flush=True)
    
    # download the original dicoms
    with tempfile.TemporaryDirectory() as workdir:
        downloaded_files = list()
        for acq in acquisitions:
            files = acq.files
            for f in files:
                if f.type == 'dicom' and f.name.endswith('dicom.zip'):
                    dest_file = workdir + '/' + f.name
                    fw.download_file_from_acquisition(acq.id, f.name, dest_file = dest_file)
                    downloaded_files.append(dest_file)

        # unzip all the files we just downloaded
        # all individual dicoms should have unique names, so collisions aren't expected
        for f in downloaded_files:
            with zipfile.ZipFile(f, 'r') as zip:
                zip.extractall(workdir)
            os.remove(f)

        # put all the files we just extracted into a single new zipfile
        merged_zip = workdir + '/' + new_acquisition_label + '.dicom.zip'
        with zipfile.ZipFile(merged_zip, 'w') as newzip, os.scandir(workdir) as dir:
            for file in dir:
                if file.name.endswith('.dcm') and file.is_file():
                    newzip.write(file.path)

        # create a new acquisition
        merged_acq = fw.add_acquisition(flywheel.models.acquisition.Acquisition(label=new_acquisition_label, session=session.id))

        # upload our merged dicom to the acquisition
        fw.upload_file_to_acquisition(merged_acq, merged_zip)
    
    # rename or delete the old acquisitions
    for acq in acquisitions:
        new_name_acq = flywheel.models.acquisition.Acquisition(label=acq.label + '_DELETE', session=session.id)
        fw.modify_acquisition(acq.id, new_name_acq)

def check_merge_ok(source_acqs, dest_acq_label, all_acqs):
    # Confirm that the source acquisitions each have one and only one dicom
    for acq in source_acqs:
        dicom_count = 0
        for f in acq.files:
            if f.type == 'dicom' and f.name.endswith('dicom.zip'):
                dicom_count += 1
        assert dicom_count == 1
    
    # check that there isn't already an acquisition with our new acquisition label
    acqs_labels = list(map(lambda acq: acq.label, all_acqs))
    assert dest_acq_label not in acqs_labels
    
def new_acquisition_label(orig_label_pattern):
    prefix = orig_label_pattern.split('_')[0]
    if prefix == 'ER1':
        return 'ER'
    return prefix

def get_sessions(page=1):
    if session_id != '':
        if page == 1:
            return [(fw.get_session(session_id))]
        else:
            return []
    elif all_sessions:
        return fw.get_project_sessions(project.id, limit=100, page=page)
    else:
        print('You must either provide a session id or process all sessions. Exiting.', flush=True)
        sys.exit(1)

page = 1
sessions = get_sessions(page)
while len(sessions) > 0:
    for sess in sessions:
        print(f'Checking {sess.subject.label}/{sess.label}.', flush=True)
        acquisitions = fw.get_session_acquisitions(sess.id)
        for pattern in acq_merge_patterns:
            try:
                to_merge = get_acquisitions_to_merge(pattern, acquisitions)
                if len(to_merge) > 0:
                    new_label = new_acquisition_label(pattern.pattern)
                    check_merge_ok(to_merge, new_label, acquisitions)
                    merge_acquisitions(to_merge, new_label, sess)
            except AssertionError:
                print(f'Could not merge {pattern} in {sess.subject.label}/{sess.label}. Check to make sure there were 3 original acquisitions, that each original acquisition has one and only one dicom file and that no acquisition with the name {new_label} exists in the session.', flush=True)
            
    page += 1
    sessions = get_sessions(page=page)


