import requests
import json
import pandas as pd
import flywheel


API_KEY = 'YOUR_FHYWHEEL_API_KEY'
fw = flywheel.Flywheel(API_KEY)


def get_sessions_from_fw(project_id):
    """
    Get all sessions from flywheel in a given project using Flywheel Swagger REST APIs
    NOTE: You can also use Flywheel SDK to retrieve sessions of a project
    :param project_id: flywheel project id
    """
    print("Retrieving sessions from Flywheel...")
    host = "https://uscdni.flywheel.io"
    session_api = "/api/sessions"
    get_sessions_url = host + session_api
    params = {'filter': "parents.project="+project_id}
    headers = {
        'Authorization': 'scitran-user ' + API_KEY ,
        'Content-type': 'application/json'
    }
    response = requests.get(get_sessions_url, params=params, headers=headers)
    response_json_data = json.loads(response.text)
    print("Retrieved all sessions")
    return response_json_data


def read_mapping_data(file):
    """
    Read the excel file which contain mapping rule for subjects and sessions whose labels need to be changed.
    Schema of input excel file: [dni_number, subject_number, session, project, need to change]
    :param file: file with the mapping rule
    """
    mapping_df = pd.read_excel(file, sheetname=0)
    mapping_list = mapping_df.values.tolist()
    mapping_dict = {}
    for row in mapping_list:
        key = str(row[0]) # key as "dni id"
        mapping_dict[key] = row
    return mapping_dict


def rename_data(fw_sessions_json_data, mapping_dict_data, fw_subject_label_set):
    """
    Rename the subject label and session label as per rules defined in mapping data
    """
    print("Modifying the subject and session labels...")
    for each_session in fw_sessions_json_data:
        dni = str(each_session["subject"]["label"])
        sub_end = "MM"
        dni = dni[:-len(sub_end)] if dni.endswith(sub_end) else dni
        session_id = each_session["_id"]
        if dni in mapping_dict_data:
            print("Modified subject label:", each_session["subject"]["code"], " to new label:",
                  mapping_dict_data[dni][1], ", Modified session label:", each_session["label"],
                  " to new label:", mapping_dict_data[dni][2])

            new_subject_code = str(mapping_dict_data[dni][1])
            each_session["subject"]["code"] = new_subject_code
            each_session["subject"]["label"] = new_subject_code
            each_session["label"] = str(mapping_dict_data[dni][2])

            result_status = upload_modified_sessions_to_fw(each_session["_id"], each_session)

            if not result_status:
                # move session to new subject
                session = fw.get_session(session_id)
                project = fw.get_project(session.project)
                subject = project.subjects.find_one('code="{}"'.format(new_subject_code))
                session.update({'subject': {'_id': subject.id}})
                print("Session moved to new subject by label:", new_subject_code)

    print("Modifications completed...")
    return fw_sessions_json_data


def upload_modified_sessions_to_fw(session_id, session_data):
    """
    Update session data for session id using Swagger REST API.
    You can use Flywheel SDK also for this
    """

    # prepare request
    host = "https://uscdni.flywheel.io"
    session_update_api = "/api/sessions" + "/" + session_id
    update_session_url = host + session_update_api
    headers = {
        'Authorization': 'scitran-user uscdni.flywheel.io:pLFRxBNOXBUeS19cK4',
        'Content-type': 'application/json'
    }

    not_allowed_properties = set(['info_exists', 'files', 'group', 'tags', 'notes', 'created', 'modified', 'parents', '_id', 'permissions'])
    # remove invalid session metadata
    for key, value in session_data.items():
        if key in not_allowed_properties:
            del session_data[key]

    # remove invalid subject metadata
    subject_id = session_data['subject']['_id']
    for key, value in session_data['subject'].items():
        if key in not_allowed_properties:
            del session_data['subject'][key]

    # send request to upload modified session label and subject label
    json_data = json.dumps(session_data)

    try:
        response = requests.put(update_session_url, headers=headers, data=json_data)
        response_json_data = json.loads(response.text)
        if response_json_data['status_code'] == 200:
            print("Data uploaded correctly for session id:", session_id, ", with response as:", response_json_data)
        else:
            print("Invalid request for session id:", session_id, ", with data:", session_data)
            if 'already exists' in response_json_data['message']:
                return False
    except:
        print("Invalid request for session id:", session_id, ", with data:", session_data)

    return True


if __name__ == '__main__':
    HRVT_project_id = "5b69097f9760d400161f73b2"

    project = fw.get_project(HRVT_project_id)
    fw_subject_label_set = set()
    for subject in project.subjects():
        fw_subject_label_set.add(subject.label)

    fw_sessions_data = get_sessions_from_fw(HRVT_project_id)

    mapping_file = "SubjectID_flywheel.xlsx"
    mapping_data_df = read_mapping_data(mapping_file)

    modified_session_data = rename_data(fw_sessions_data, mapping_data_df, fw_subject_label_set)
