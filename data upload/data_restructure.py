import os
import pandas as pd
import numpy as np
import time
import shutil
from distutils.dir_util import copy_tree


class Data_Upload:
    def __init__(self, project_id_path):
        self.project_path = project_id_path
        self.sub_path_dict = {}
        self.pre_ses_path_dict = {}
        self.post_ses_path_dict = {}
        self.sub_ses_mapping_filepath = "./resources/subID_mriID.xlsx" # path of subjects ids and session ids
        self.data_path = "D:/Research/Emotion_lab/task_Hyun/2018_HRVT_MRI_Study/pre-training" # Path of folder where data resides
        self.name_change_dict = {
            "ASL_Control":"Wholebrain_ASL",
            "ASL_Control_Perfusion_Weighted":"Perfusion_Weighted",
            "t2w4radiology_5":"t2w4radiology",
            "LC_AP":"ep2d_se_task_AP",
            "LC_PA":"ep2d_se_task_PA",
            "MPRAGE":"t1_mprage_short",
            "Localizers_1":"Localizers",
            "ASL_TM":"Wholebrain_ASL_TM",
            "ASL_TM_Perfusion_Weighted":"Perfusion_Weighted_TM"
        }
        self.pre_subject_min = 9816
        self.pre_subject_max = 10102
        self.post_subject_min = 9868
        self.post_subject_max = 10069

    def rchop(self, s, sub):
        return s[:-len(sub)] if s.endswith(sub) else s

    def move_dicom_files(self):
        subjectsList = os.listdir(self.project_path)
        for subject in subjectsList:
            print("Start moving dicom files for subject :" + str(subject))
            subject_id_path = os.path.join(self.project_path, subject)
            sessionsList = os.listdir(subject_id_path)
            for session in sessionsList:
                session_id_path = os.path.join(subject_id_path, session)
                acquisitionsList = os.listdir(session_id_path)
                for acquisition in acquisitionsList:
                    try:
                        acquisition_path = os.path.join(session_id_path, acquisition)
                        dicom_folder_path = os.path.join(acquisition_path, "dicom")
                        os.makedirs(dicom_folder_path)
                        datafilesList = os.listdir(acquisition_path)
                        for datafile in datafilesList:
                            if datafile.endswith('.dcm'):
                                existing_datafile_path = os.path.join(acquisition_path, datafile)
                                new_datafile_path = os.path.join(dicom_folder_path,datafile)
                                shutil.move(existing_datafile_path, new_datafile_path)
                    except:
                        print("Files coud not be copied for acquisition:" + acquisition_path)
                        continue

    def rename_acquisitions(self):
        subjectsList = os.listdir(self.project_path)
        for subject in subjectsList:
            subject_id_path = os.path.join(self.project_path, subject)
            sessionsList = os.listdir(subject_id_path)
            for session in sessionsList:
                print("Start renaming for session :" + str(session))
                session_id_path = os.path.join(subject_id_path, session)
                acquisitionsList = os.listdir(session_id_path)
                for acquisition in acquisitionsList:
                    if acquisition in self.name_change_dict:
                        existing_acquisition_path = os.path.join(session_id_path, acquisition)
                        new_acquisition_path = os.path.join(session_id_path,
                                                            self.name_change_dict[acquisition])
                        os.rename(existing_acquisition_path, new_acquisition_path)
                        # print("name changed from" + existing_acquisition_path + " to " + new_acquisition_path)
                print("Renaming done for session :" + str(session))

    def copy_data(self):
        print("Copying data...")
        listOfFiles_to_copy = os.listdir(self.data_path)
        for file_to_copy in listOfFiles_to_copy:
            ses_id = self.rchop(file_to_copy, 'Mm')
            ses_id = self.rchop(ses_id, 'MM')
            try:
                ses_id = int(ses_id)
            except:
                print("session id" + str(ses_id) + " can't be converted to integer :")
                continue
            print("Coping data for session id:" + str(ses_id))
            ses_id_path = None
            if ses_id_path is None and ses_id in self.pre_ses_path_dict:
                ses_id_path = self.pre_ses_path_dict[ses_id]
            if ses_id_path is None and ses_id in self.post_ses_path_dict:
                ses_id_path = self.post_ses_path_dict[ses_id]
            if ses_id_path is not None:
                src_folder = os.path.join(self.data_path, file_to_copy)
                dest_folder = ses_id_path
                copy_tree(src_folder, dest_folder)
                print("Copied data for session id:" + str(ses_id))
            else:
                print("Coping data not possible for session id:" + str(ses_id))

    def remove_sessions(self):
        subjectsList = os.listdir(self.project_path)
        for subject in subjectsList:
            subject_id_path = os.path.join(self.project_path, subject)
            sessionsList = os.listdir(subject_id_path)
            for session in sessionsList:
                if session == "post":
                    session_id_path = os.path.join(subject_id_path, session)
                    shutil.rmtree(session_id_path)
                # acquisitionsList = os.listdir(session_id_path)
                # if acquisitionsList is None or len(acquisitionsList) == 0:
                #     shutil.rmtree(session_id_path)

    def remove_subjects(self):
        subjectsList = os.listdir(self.project_path)
        for subject in subjectsList:
            subject_id_path = os.path.join(self.project_path, subject)
            sessionsList = os.listdir(subject_id_path)
            if sessionsList is None or len(sessionsList) == 0:
                shutil.rmtree(subject_id_path)

    def create_subjects(self):
        print("create subjects now")
        subject_col = "subject_number"
        pre_session_col = "Pre_dni_number"
        post_session_col = "Post_dni_number"

        mapping_df = pd.read_excel(self.sub_ses_mapping_filepath)
        mapping_df = mapping_df.replace(np.nan, -1)
        for index, row in mapping_df.iterrows():
            subject_id = int(row[subject_col]) if row[subject_col] is not None else 0
            subject_id_path = os.path.join(self.project_path, str(subject_id))
            os.makedirs(subject_id_path)
            self.sub_path_dict[subject_id] = subject_id_path

            if row[pre_session_col] != -1:
                pre_session_id = int(row[pre_session_col])
                if pre_session_id >= self.pre_subject_min and pre_session_id <= self.pre_subject_max:
                    pre_ses_path = os.path.join(subject_id_path, "pre")
                    os.makedirs(pre_ses_path)
                    self.pre_ses_path_dict[pre_session_id] = pre_ses_path

            if row[post_session_col] != -1:
                post_session_id = int(row[post_session_col])
                if pre_session_id >= self.post_subject_min and pre_session_id <= self.post_subject_max:
                    post_ses_path = os.path.join(subject_id_path, "post")
                    os.makedirs(post_ses_path)
                    self.post_ses_path_dict[post_session_id] = post_ses_path

        print(self.post_ses_path_dict)


if __name__ == '__main__':
    start_time = time.time()
    # base_path = "./resources"
    base_path = "."

    # create group id folder
    group_id = "emocog"
    group_id_path = os.path.join(base_path, group_id)
    if not os.path.isdir(group_id_path):
        os.makedirs(group_id_path)

    # create project folder
    project_id = "2018_HRVT_2"
    project_id_path = os.path.join(group_id_path, project_id)
    if not os.path.isdir(project_id_path):
        os.makedirs(project_id_path)

    # create subjects, sessions
    obj = Data_Upload(project_id_path)
    obj.create_subjects()

    # remove session folders for which no acquisition no be uploaded
    # obj.remove_sessions()

    # remove subjects folders for which no sessions no be uploaded
    # obj.remove_subjects()

    # copy data
    obj.copy_data()

    # rename acquisition folder names
    obj.rename_acquisitions()

    # move dicom files under separate dicom folder
    obj.move_dicom_files()

    end_time = time.time()
    run_time = end_time - start_time
    print("Run time in seconds: " + str(run_time))

