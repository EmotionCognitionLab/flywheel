from chalice import Chalice, CORSConfig
import flywheel
import json

app = Chalice(app_name='fw-mark-outputs')
fw_api_key_header = 'X-FW-API-KEY'
cors_config = CORSConfig(allow_headers=[fw_api_key_header])

def fw_client(req):
    api_key = req.headers[fw_api_key_header]
    _fw = flywheel.Client(api_key)
    return _fw

@app.route('/projects', cors=cors_config)
def projects():
    fw = fw_client(app.current_request)
    projects = fw.projects()
    ids_and_labels = [ { 'id': x.id, 'label': x.label } for x in projects ]
    ids_and_labels.sort(key= lambda item: item['label'] )
    return ids_and_labels

file_fun = lambda files: [{'id':f.id, 'name':f.name} for f in files] if files is not None else []

@app.route('/projects/{id}', cors=cors_config)
def projectData(id):
    fw = fw_client(app.current_request)
    analyses = fw.get_analyses('projects', id, 'sessions')
    # filter out info we don't need
    analyses_filtered = [{
            'id': x.id,
            'files': file_fun(x.files),
            'label': x.label,
            'parent': x.parent.id
            } for x in analyses]
    result = {}
    analyses_filtered.sort(key=lambda item: item['label'])
    result['analyses'] = analyses_filtered

    session_ids = set([x['parent'] for x in analyses_filtered])
    sessions = []
    for sess_id in session_ids:
            sess = fw.get_session(sess_id)
            sessions.append({
                    'id': sess_id,
                    'label': sess.label,
                    'subject_id': sess.subject.id,
                    'subject_label': sess.subject.label
                    })
    sessions.sort(key=lambda item: item['subject_label'])
    result['sessions'] = sessions

    proj = fw.get_project(id)
    result['label'] = proj.label
    return result

@app.route('/projects/{id}/analyses', cors=cors_config, methods=['GET'])
def analysesForProject(id):
    fw = fw_client(app.current_request)
    analyses = fw.get_analyses('projects', id, 'sessions')
    if len(analyses) == 0: return []

    # filter out info we don't need
    analyses_filtered = [{
            'id': x.id,
            'files': file_fun(x.files),
            'label': x.label,
            'parent': x.parent.id
            } for x in analyses]
    analyses_filtered.sort(key=lambda item: item['label'])

    return analyses_filtered

@app.route('/projects/{id}/sessions', cors=cors_config, methods=['GET'])
def sessionsForProject(id):
    fw = fw_client(app.current_request)
    proj = fw.get(id)
    result = { 'project_label': proj.label }
    result['sessions'] = []
    for sess in proj.sessions.iter():
        result['sessions'].append({
            'id': sess.id,
            'label': sess.label,
            'subject_id': sess.subject.id,
            'subject_label': sess.subject.label,
            'acquisitions': [],
            'analyses': []
        })
    result['sessions'].sort(key=lambda item: item['subject_label']+item['label'])

    return result

@app.route('/projects/{id}/acquisitions', cors=cors_config, methods=['GET'])
def acquisitionsForProject(id):
    page = int(app.current_request.query_params['page']) if app.current_request.query_params and app.current_request.query_params['page'] else 1
    limit = 1000
    fw = fw_client(app.current_request)
    acqs = fw.get_all_acquisitions(filter=f'parents.project={id}', page=page, limit=limit)
    if len(acqs) == 0: return {'acquisitions': [], 'nextPage': -1}

    result = {}
    result['nextPage'] = page + 1 if len(acqs) >= limit else -1
    acqs_filtered = [{
        'id': x.id,
        'files': file_fun(x.files),
        'label': x.label,
        'parent': x.parents.session
    } for x in acqs]
    result['acquisitions'] = acqs_filtered
    return result

@app.route('/sessions/{id}/acquisitions', cors=cors_config, methods=['GET'])
def acquisitionsForSession(id):
    fw = fw_client(app.current_request)
    acqs = fw.get_all_acquisitions(filter=f'parents.session={id}')
    if len(acqs) == 0: return {'acquisitions': []}

    return [{
        'id': x.id,
        'files': file_fun(x.files),
        'label': x.label,
        'parent': x.parents.session
    } for x in acqs]

@app.route('/projects/{id}/file/upload', cors=cors_config, methods=['POST'])
def uploadFileToProject(id):
    fw = fw_client(app.current_request)
    data = app.current_request.json_body
    file_spec = flywheel.FileSpec(data['name'], json.dumps(data['content']), data['contentType'])
    proj = fw.get_project(id)
    proj.upload_file(file_spec)
    return {}
