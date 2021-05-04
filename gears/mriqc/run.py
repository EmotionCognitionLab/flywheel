#!/usr/bin/env python3

import flywheel
import os
import shutil
import subprocess
import tempfile

container = '[matherlab/mriqc]'
print(container, ' initiated', flush=True)

input_dir = '/flywheel/v0/input'
output_dir = '/flywheel/v0/output'

context = flywheel.GearContext()
fw = context.client
destination = fw.get(context.destination['id'])
project = fw.get_project(destination.parents.project)
project_label = project.label
ignore_errors = context.config['ignore_errors']
acquisition_label_regex = context.config['acquisition_label_regex']
if acquisition_label_regex == '':
    acquisition_label_regex = None


def find_mriqc_json_files(proj_name, acq_label_regex=None):
    query = 'project.label = {proj_name} and file.name contains mriqc.json'.format(proj_name=proj_name)
    if acq_label_regex:
        query = query + ' and acquisition.label =~ "{acq_label_regex}"'.format(acq_label_regex=acq_label_regex)
    print('Query for mriqc.json files: {query}'.format(query=query))
    return fw.search({'structured_query': query, 'return_type': 'file'}, size=10000)


# For each mriqc json file, get the BIDS info from the corresponding nifti file and
# use it to name the json file
def mriqc_json_to_bids(query_results, ignore_errors, dest_dir):
    inputs = []
    for item in query_results:
        if not item['file']['name'].endswith('_mriqc.json'):
            raise ValueError("Expoected an mriqc.json file, but found {item['file']['name']}".format(item=item))

        sess = item['session']['label']
        subj = item['subject']['code']
        acq_id = item['parent'].to_dict()['id']
        acq = fw.get_acquisition(acq_id)
        fname = item['file']['name']
        fpath = '{subj}/{sess}/{acq.label} ({acq_id}) /{fname}'.format(subj=subj, sess=sess, acq=acq, acq_id=acq_id, fname=fname)
        print('Including {fpath}'.format(fpath=fpath), flush=True)

        try:
            (base_name, _) = fname.split('_mriqc.json')
            nifti_meta = fw.get_acquisition_file_info(acq_id, '{base_name}.nii.gz'.format(base_name=base_name))
            bids_info = nifti_meta['info'].get('BIDS', None)
            if not bids_info or bids_info == 'NA':
                err_msg = 'BIDS info is missing for {base_name}.nii.gz .'.format(base_name=base_name)
                if ignore_errors:
                    print('\t Skipping. {err_msg}'.format(err_msg=err_msg), flush=True)
                    continue
                else:
                    raise Exception(err_msg)
            bids_filename = nifti_meta['info']['BIDS']['Filename'].replace('.nii.gz', '.json')
            bids_path = nifti_meta['info']['BIDS']['Path']
            bids_dest_dir = os.path.join(dest_dir, bids_path)
            bids_full_path = os.path.join(bids_dest_dir, bids_filename)
            os.makedirs(bids_dest_dir, exist_ok=True)
            if os.path.exists(bids_full_path):
                err_msg = '{bids_filename} already exists'.format(bids_filename=bids_filename)
                if ignore_errors:
                    print('\tSkipping. {err_msg}'.format(err_msg=err_msg), flush=True)
                else:
                    raise Exception(err_msg)
            fw.download_file_from_acquisition(acq_id, item['file']['name'], bids_full_path)
            inputs.append(fpath)
        except KeyError as ke:
            print("Error trying to download {fname} from {subj}/{sess}/{acq.label}. Check to make sure a corresponding nifti file exists, that you have run BIDS curation and that the nifti file has BIDS.Filename and BIDS.Path correctly set.".format(fname=fname, subj=subj, sess=sess, acq=acq), flush=True)
            print('Missing key: {ke}'.format(ke=ke), flush=True)
            if ignore_errors:
                continue
            else:
                raise Exception('Error trying to download {fname} from {subj}/{sess}/{acq.label}, probably due to incorrect/missing BIDS metadata in corresponding nifti file.'.format(fname=fname, subj=subj, sess=sess, acq=acq))
    
    return inputs

res = find_mriqc_json_files(project_label, acquisition_label_regex)
with tempfile.TemporaryDirectory() as tmpdir: 
    input_files = mriqc_json_to_bids(res, ignore_errors, tmpdir)
    subprocess.run(['mriqc', input_dir, tmpdir, 'group'], check=True)
    outfiles = ['group_T1w.html', 'group_T1w.tsv', 'group_bold.html', 'group_bold.tsv']
    outpaths = [os.path.join(tmpdir, f) for f in outfiles]
    # saved_output_files = []
    for (f, p) in zip(outfiles, outpaths):
        print('Checking {p}'.format(p=p))
        if os.path.exists(p):
            saved_path = os.path.join(output_dir, f)
            print('{p} exists, copying to {saved_path}'.format(p=p, saved_path=saved_path))
            shutil.copy(p, saved_path)
            # saved_output_files.append(saved_path)

    fw.modify_analysis_info(destination, {'set': {'inputs': input_files}})

