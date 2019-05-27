import pandas as pd
import flywheel


API_KEY = 'YOUR_FLYWHEEL_API_KEY_HERE'
fw = flywheel.Flywheel(API_KEY)


def move_project_sessions_to_other_project(src_project_id, dest_project_id):
    """
    Move all sessions from source project to destination project
    """
    src_project = fw.get_project(src_project_id)
    dest_project = fw.get_project(dest_project_id)
    dest_project_sessions = dest_project.sessions()
    dest_project_subj_ses_label_set = set()
    for dest_session in dest_project_sessions:
        dest_project_subj_ses_label_set.add(dest_session["subject"]["label"]+"_"+dest_session["label"])

    for src_session in src_project.sessions():
        src_subject_code = src_session["subject"]["code"]
        src_session_label = src_session["label"]
        src_sub_ses_label = src_subject_code + "_" + src_session_label
        if src_sub_ses_label in dest_project_subj_ses_label_set:
            print("Session already exist with same subject and session label... session id:", src_session["_id"])
            continue
        else:
            try:
                dest_subject = find_or_create_subject(fw, src_session, dest_project_id, src_subject_code)
                move_session_to_subject(src_session, dest_subject)
                print("Session with subject label " + src_subject_code + " and session label " + src_session_label + " moved to new project")
            except:
                print("Error while processing subject code:",src_subject_code, " and session label: ", src_session_label)


def move_session_to_subject(session, subject):
    session.update({'subject': {'_id': subject.id}})


def find_or_create_subject(fw, session, project_id, subject_code):
    """
    Try to find if a subject with that code already exists in the project
    """
    project = fw.get_project(project_id)
    subject = project.subjects.find_first('code="{}"'.format(subject_code))

    if not subject:
        # if it doesn't, make one with the same metadata
        old_subject = session.subject
        new_subject = flywheel.Subject(project=project_id, firstname=old_subject.firstname, code=subject_code,
                                       lastname=old_subject.lastname, sex=old_subject.sex,
                                       cohort=old_subject.cohort, ethnicity=old_subject.ethnicity,
                                       race=old_subject.race, species=old_subject.species,
                                       strain=old_subject.strain, files=old_subject.files)
        response = fw.add_subject(new_subject)
        subject = fw.get_subject(response)

    return subject


def read_mapping_data(file):
    """
    Read the excel file which contain mapping rule for subjects and sessions. Contains
    schema of input excel file: [dni_number, subject_number, session, project, need to change]
    :param file: file with the mapping rule
    """
    mapping_df = pd.read_excel(file, sheetname=0)
    mapping_list = mapping_df.values.tolist()
    mapping_dict = {}
    for row in mapping_list:
        key = str(row[1]) + "_" + str(row[2])# key as "subjectid_sessionid"
        mapping_dict[key] = row
    return mapping_dict


def update_last_name_in_fw(project_id, mapping_data_dict):
    """
    Update last name in session metadata raw field
    :param project_id: projecct id of flywheel project
    :param mapping_data_dict: contains key as "subjectid_sessionid" and
    value as row entry from mapping file [dni_number, subject_number, session, project, need to change]
    """
    project = fw.get_project(project_id)
    for session in project.sessions():
        try:
            session_label = session["label"]
            subject_label = session["subject"]["label"]
            key = subject_label + "_" + session_label
            if key not in mapping_data_dict:
                print("There is no dni number available to provide as last name for subject label " + subject_label +
                  " and session label " + session_label)
                continue
            else:
                new_last_name = str(mapping_data_dict[key][0])
                session.update({'info': {'subject_raw': {'lastname': new_last_name}}})
                print("Session with subject label " + subject_label +
                      " and session label " + session_label +
                      " updated it's last name to " + new_last_name)
        except:
            print("Error while processing last name for session: ",session["_id"])


if __name__ == '__main__':
    src_projecct_id = "5c05ac327bdf49001573b7ce" # currently it is set to 2018_HRVT_2 project
    dest_project_id = "5b69097f9760d400161f73b2" # currently it is set of 2018_HRVT project

    move_project_sessions_to_other_project(src_projecct_id, dest_project_id)

    mapping_file = "SubjectID_flywheel.xlsx"
    mapping_data_dict = read_mapping_data(mapping_file)

    update_last_name_in_fw(dest_project_id, mapping_data_dict)
    print("Tasks completed...")
