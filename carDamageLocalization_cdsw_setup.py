#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import math
import os
import re
import requests
import sys
import time

PUBLIC_IP = sys.argv[1]
MODEL_PKL_FILE = sys.argv[2]
if len(sys.argv) > 3:
    PASSWORD = open(sys.argv[3]).read()
else:
    PASSWORD = os.environ['THE_PWD']

PROJECT_ZIP_FILE = os.environ.get('PROJECT_ZIP_FILE', None)

BASE_DIR = os.path.dirname(__file__) if os.path.dirname(__file__) else '.'
_IS_TLS_ENABLED = os.path.exists(os.path.join(BASE_DIR, '.enable-tls'))

TRUSTSTORE = '/opt/cloudera/security/x509/truststore.pem'
URL_SCHEME = 'https' if _IS_TLS_ENABLED else 'http'

CDSW_API = URL_SCHEME + '://cdsw.{}.nip.io/api/v1'.format(PUBLIC_IP, )
CDSW_ALTUS_API = URL_SCHEME + '://cdsw.{}.nip.io/api/altus-ds-1'.format(PUBLIC_IP, )

_DEFAULT_PROJECT_NAME = 'carDamageLocalization-Workshop'

USERNAME = 'admin'
FULL_NAME = 'Workshop Admin'
EMAIL = 'admin@cloudera.com'

_MODEL_NAME = 'car Damage Localization'

_CDSW_SESSION = requests.Session()
_RELEASE = []
_RUNTIMES = {}
_DEFAULT_RUNTIME = 0
_VIZ_RUNTIME = 0
_MODEL = {}
_DEFAULT_PROJECT = {}
_VIZ_PROJECT = {}

_UPLOAD_CHUNK_SIZE = 1048576



def _init_sessions():
    global _CDSW_SESSION
    global _VIZ_SESSION
    global _IS_TLS_ENABLED
    print("Initializing sessions")
    if _IS_TLS_ENABLED:
        print("Setting truststore")
        _CDSW_SESSION.verify = TRUSTSTORE
        _VIZ_SESSION.verify = TRUSTSTORE


def _authorize_sessions():
    global _CDSW_SESSION
    print("Authorizing sessions")
    resp = _cdsw_post(CDSW_API + '/authenticate',
                      json={'login': USERNAME, 'password': PASSWORD})
    token = resp.json()['auth_token']
    _CDSW_SESSION.headers.update({'Authorization': 'Bearer ' + token})


def _get_release():
    global _RELEASE
    if not _RELEASE:
        resp = _cdsw_get(CDSW_API + '/site/stats')
        release_str = [c['value'] for c in resp.json() if c['key'] == 'config.release'][0]
        _RELEASE = [int(v) for v in release_str.split('.')]
        print('CDSW release: {}'.format(_RELEASE))
    return _RELEASE


def _get_runtimes(refresh=False):
    global _RUNTIMES
    if not _RUNTIMES or refresh:
        resp = _cdsw_get(CDSW_API + '/runtimes?includeAll=true', expected_codes=[200, 501])
        if resp.status_code == 200:
            _RUNTIMES = resp.json()['runtimes']
        elif resp.status_code == 501:
            _RUNTIMES = []
            print("List of runtimes not available yet.")
    return _RUNTIMES


def _find_runtime(editor, kernel, edition, short_version, retries=600):
    total_retries = retries
    while True:
        runtimes = _get_runtimes(refresh=True)
        selected = [runtime for runtime in runtimes
                    if runtime['editor'] == editor and runtime['kernel'] == kernel and runtime['edition'] == edition
                    and runtime['shortVersion'] == short_version]
        if selected:
            return selected[0]['id']
        retries -= 1
        if retries <= 0:
            break
        print('Could not find the required runtime among the {} retrieved ones.'
              'Will retry (#{} out of {} attempts).'.format(len(runtimes), retries, total_retries))
        time.sleep(1)
    raise RuntimeError('Could not find the required runtime. Giving up. Available runtimes: {}'.format(runtimes))


def _get_default_runtime():
    global _DEFAULT_RUNTIME
    if not _DEFAULT_RUNTIME:
        _DEFAULT_RUNTIME = _find_runtime('Workbench', 'Python 3.8', 'Standard', '2022.04')
        print('Default Runtime ID: {}'.format(_DEFAULT_RUNTIME, ))
    return _DEFAULT_RUNTIME



def _get_model(refresh=False):
    global _MODEL_NAME
    global _MODEL
    if not _MODEL or refresh:
        resp = _cdsw_post(CDSW_ALTUS_API + '/models/list-models',
                          json={
                              'projectOwnerName': 'admin',
                              'latestModelDeployment': True,
                              'latestModelBuild': True,
                          })
        models = [m for m in resp.json() if m['name'] == _MODEL_NAME]
        if models:
            _MODEL = models[0]
        else:
            _MODEL = {}
    return _MODEL


def _is_model_deployed():
    model = _get_model(refresh=True)
    return model and model['latestModelDeployment']['status'] == 'deployed'


def _rest_call(func, url, expected_codes=None, **kwargs):
    if not expected_codes:
        expected_codes = [200]
    resp = func(url, **kwargs)
    if resp.status_code not in expected_codes:
        print(resp.text)
        raise RuntimeError("Unexpected response: {}".format(resp))
    return resp


def _cdsw_get(url, expected_codes=None, **kwargs):
    global _CDSW_SESSION
    return _rest_call(_CDSW_SESSION.get, url, expected_codes, **kwargs)


def _cdsw_post(url, expected_codes=None, **kwargs):
    global _CDSW_SESSION
    return _rest_call(_CDSW_SESSION.post, url, expected_codes, **kwargs)


def _cdsw_put(url, expected_codes=None, **kwargs):
    global _CDSW_SESSION
    return _rest_call(_CDSW_SESSION.put, url, expected_codes, **kwargs)


def _cdsw_patch(url, expected_codes=None, **kwargs):
    global _CDSW_SESSION
    return _rest_call(_CDSW_SESSION.patch, url, expected_codes, **kwargs)


def _cdsw_delete(url, expected_codes=None, **kwargs):
    global _CDSW_SESSION
    return _rest_call(_CDSW_SESSION.delete, url, expected_codes, **kwargs)


def _get_project(name=None, project_id=None):
    if (not name and not project_id) or (name and project_id):
        raise RuntimeError("Must specify either name or id, but not both.")
    resp = _cdsw_get(CDSW_API + '/users/admin/projects')
    for proj in resp.json():
        if (name and proj['name'] == name) or (project_id and proj['id'] == project_id):
            return proj
    return {}


def _create_github_project():
    return _cdsw_post(CDSW_API + '/users/admin/projects', expected_codes=[201, 502],
                      json={'template': 'git',
                            'project_visibility': 'private',
                            'name': _DEFAULT_PROJECT_NAME,
                            'gitUrl': 'https://github.com/bguedes/carDamageLocalizationPredictionML.git'})


def _create_local_project(zipfile):
    token = str(time.time())[:9]
    filename = os.path.basename(zipfile)
    total_size = os.stat(zipfile).st_size
    total_chunks = math.ceil(total_size / _UPLOAD_CHUNK_SIZE)

    f = open(zipfile, 'rb')
    chunk = 0
    while True:
        buf = f.read(_UPLOAD_CHUNK_SIZE)
        if not buf:
            break
        chunk += 1
        chunk_size = len(buf)
        _cdsw_post(CDSW_API + '/upload/admin', expected_codes=[200],
                   data={
                       'uploadType': 'archive',
                       'uploadToken': token,
                       'flowChunkNumber': chunk,
                       'flowChunkSize': chunk_size,
                       'flowCurrentChunkSize': chunk_size,
                       'flowTotalSize': total_size,
                       'flowIdentifier': token + '-' + filename,
                       'flowFilename': filename,
                       'flowRelativePath': filename,
                       'flowTotalChunks': total_chunks,
                   },
                   files={'file': (filename, io.BytesIO(buf), 'application/zip')}
                   )

    return _cdsw_post(CDSW_API + '/users/admin/projects', expected_codes=[201],
                      json={
                          "name": _DEFAULT_PROJECT_NAME,
                          "project_visibility": "private",
                          "template": "local",
                          "isPrototype": False,
                          "supportAsync": True,
                          "avoidNameCollisions": False,
                          "uploadToken": token,
                          "fileName": filename,
                          "isArchive": True
                      })


def _get_default_project():
    global _DEFAULT_PROJECT
    if not _DEFAULT_PROJECT:
        _DEFAULT_PROJECT = _get_project(name=_DEFAULT_PROJECT_NAME)
    return _DEFAULT_PROJECT



def start_model(build_id):
    _cdsw_post(CDSW_ALTUS_API + '/models/deploy-model', json={
        'modelBuildId': build_id,
        'cpuMillicores': 1000,
        'memoryMb': 4096,
    })



CSRF_REGEXPS = [
    r'.*name="csrfmiddlewaretoken" type="hidden" value="([^"]*)"',
    r'.*"csrfmiddlewaretoken": "([^"]*)"',
    r'.*\.csrf_token\("([^"]*)"\)'
]


def _get_csrf_token(txt, quiet=False):
    token = None
    for regexp in CSRF_REGEXPS:
        m = re.match(regexp, txt, flags=re.DOTALL)
        if m:
            token = m.groups()[0]
            break
    else:
        if not quiet:
            raise RuntimeError("Cannot find CSRF token.")
    return token



def main():
    print('BASE_DIR:       {}'.format(BASE_DIR))
    print('CDSW_ALTUS_API: {}'.format(CDSW_ALTUS_API))
    print('CDSW_API:       {}'.format(CDSW_API))
    print('IS_TLS_ENABLED: {}'.format(_IS_TLS_ENABLED))
    print('MODEL_PKL_FILE: {}'.format(MODEL_PKL_FILE))
    print('PASSWORD:       {}'.format(PASSWORD))
    print('PUBLIC_IP:      {}'.format(PUBLIC_IP))
    print('TRUSTSTORE:     {}'.format(TRUSTSTORE))
    print('-------------------------------------------------------')

    print('# Prepare CDSW for workshop')
    resp = None
    try:
        _init_sessions()

        print('# Create user')
        while True:
            status = ''
            try:
                resp = _cdsw_post(CDSW_API + '/users', expected_codes=[201, 404, 422, 503],
                                  json={
                                      'email': EMAIL,
                                      'name': FULL_NAME,
                                      'username': USERNAME,
                                      'password': PASSWORD,
                                      'type': 'user'
                                  },
                                  timeout=10)
                if resp.status_code == 201:
                    print('User created')
                    break
                elif resp.status_code == 422:
                    print('User admin already exists. Skipping creation.')
                    break
                else:
                    status = 'Error code: {}'.format(resp.status_code)
            except requests.exceptions.ConnectTimeout as err:
                status = 'Connection timeout. Exception: {}'.format(err)
                pass
            except requests.exceptions.ConnectionError as err:
                status = 'Connection error. Exception: {}'.format(err)
                pass
            if status:
                print('Waiting for CDSW to be ready... ({})'.format(status))
            else:
                print('Waiting for CDSW to be ready...')
            time.sleep(10)

        _authorize_sessions()

        resp = _cdsw_get(CDSW_API + '/users')
        user = [u for u in resp.json() if u['username'] == USERNAME]
        user_id = user[0]['id']
        print('User ID: {}'.format(user_id))

        print('# Check if model is already running')
        if _is_model_deployed():
            print('Model is already deployed!! Skipping.')
        else:
            print('# Add engine')
            resp = _cdsw_post(CDSW_API + '/site/engine-profiles', expected_codes=[201],
                              json={'cpu': 1, 'memory': 4})
            engine_id = resp.json()['id']
            print('Engine ID: {}'.format(engine_id, ))

            print('# Add environment variable')
            _cdsw_patch(CDSW_API + '/site/config',
                        json={'environment': '{"HADOOP_CONF_DIR":"/etc/hadoop/conf/"}'})


            print('# Add project')
            _cdsw_get(CDSW_API + '/users/admin/projects')
            if not _get_default_project():
                if PROJECT_ZIP_FILE:
                    print('Creating a Local project using file {}'.format(PROJECT_ZIP_FILE))
                    _create_local_project(PROJECT_ZIP_FILE)
                else:
                    print('Creating a GitHub project')
                    _create_github_project()
            print('Project ID: {}'.format(_get_default_project()['id'], ))

            print('# Upload setup script')
            setup_script = """!pip3 install -U -r requirements.txt"""
            _cdsw_put(CDSW_API + '/projects/admin/carDamageLocalization-Workshop/files/setup_workshop.py',
                      files={'name': setup_script})

            print('# Upload model')
            model_pkl = open(MODEL_PKL_FILE, 'rb')
            _cdsw_put(CDSW_API + '/projects/admin/carDamageLocalization-Workshop/files/models/carDamageLocalizationPredictionModel.h5',
                      files={'name': model_pkl})

            job_params = {
                'name': 'Setup workshop',
                'type': 'manual',
                'script': 'setup_workshop.py',
                'timezone': 'America/Los_Angeles',
                'environment': {},
                'kernel': 'python3',
                'cpu': 1,
                'memory': 4,
                'nvidia_gpu': 0,
                'notifications': [{
                    'user_id': user_id,
                    'success': False,
                    'failure': False,
                    'timeout': False,
                    'stopped': False
                }],
                'recipients': {},
                'attachments': [],
            }
            if _get_release() >= [1, 10]:
                job_params.update({'runtime_id': _get_default_runtime()})

            print('# Create job to run the setup script')
            resp = _cdsw_post(CDSW_API + '/projects/admin/carDamageLocalization-Workshop/jobs', expected_codes=[201],
                              json=job_params)
            job_id = resp.json()['id']
            print('Job ID: {}'.format(job_id, ))

            print('# Start job')
            job_url = '{}/projects/admin/carDamageLocalization-Workshop/jobs/{}'.format(CDSW_API, job_id)
            start_url = '{}/start'.format(job_url, )
            _cdsw_post(start_url, json={})
            while True:
                resp = _cdsw_get(job_url)
                status = resp.json()['latest']['status']
                print('Job {} status: {}'.format(job_id, status))
                if status == 'succeeded':
                    break
                elif status == 'failed':
                    raise RuntimeError('Job failed')
                time.sleep(10)

            print('# Get engine image to use for model')
            resp = _cdsw_get(CDSW_API + '/projects/admin/carDamageLocalization-Workshop/engine-images')
            engine_image_id = resp.json()['id']
            print('Engine image ID: {}'.format(engine_image_id, ))

            print('# Deploy model')
            if _get_release() >= [1, 10]:
                job_params = {
                    'runtimeId': _get_default_runtime(),
                    'authEnabled': True,
                    "addons": [],
                }
            else:
                job_params = {}
            job_params.update({
                'projectId': _get_default_project()['id'],
                'name': _MODEL_NAME,
                'description': _MODEL_NAME,
                'visibility': 'private',
                'targetFilePath': 'models/carDamageLocalizationPrediction.py',
                'targetFunctionName': 'detectDamageLocalization',
                'engineImageId': engine_image_id,
                'kernel': 'python3',
                'examples': [{'request': {
  'imageBase64': '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'}}],
                'cpuMillicores': 1000,
                'memoryMb': 4096,
                'replicationPolicy': {'type': 'fixed', 'numReplicas': 1},
                'environment': {},
            })
            resp = _cdsw_post(CDSW_ALTUS_API + '/models/create-model', json=job_params)
            try:
                model_id = resp.json()['id']
            except Exception as err:
                print(resp.json())
                raise err
            print('Model ID: {}'.format(model_id, ))

        # ================================================================================

        # See https://docs.cloudera.com/cdsw/latest/analytical-apps/topics/cdsw-application-limitations.html

        if _get_release() > [1, 9]:
            print('# Allow applications to be configured with unauthenticated access')
            resp = _cdsw_patch(CDSW_API + '/site/config',
                               json={"allow_unauthenticated_access_to_app": True})
            print('Set unauthenticated access flag to: {}'.format(resp.json()["allow_unauthenticated_access_to_app"], ))


        # ================================================================================

        print('# Wait for model to start')
        while True:
            model = _get_model(refresh=True)
            if model:
                build_status = model['latestModelBuild']['status']
                build_id = model['latestModelBuild']['id']
                deployment_status = model['latestModelDeployment']['status']
                print('Model {}: build status: {}, deployment status: {}'.format(model['id'], build_status,
                                                                                 deployment_status))
                if build_status == 'built' and deployment_status == 'deployed':
                    break
                elif build_status == 'built' and deployment_status == 'stopped':
                    # If the deployment stops for any reason, try to give it a little push
                    start_model(build_id)
                elif build_status == 'failed' or deployment_status == 'failed':
                    raise RuntimeError('Model deployment failed')
            time.sleep(10)


    except Exception as err:
        if resp:
            print(resp.text)
        raise err

    print('# CDSW setup completed successfully!')


if __name__ == '__main__':
    main()
