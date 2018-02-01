from flask import Blueprint, request

from flask_jwt_extended import jwt_required, get_raw_jwt
from lib.managers.UploadManager import UploadManager
from lib.utils.RequestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.UploadError import UploadError

upload_blueprint = Blueprint('upload', __name__)

@upload_blueprint.route('/upload', methods=['PUT', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def uploadData():
    repo_id = int(request.form.get('repo_id'))

    try:
        return makeResponse(payload=UploadManager.processUpload(repo_id), message="File uploaded")
    except UploadError as e:
        return makeResponse(error=e)

@upload_blueprint.route('/upload/import', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def importData():
    repo_id = int(request.form.get('repo_id'))
    filename = request.form.get('filename')
    original_filename = request.form.get('original_filename')
    data_mapping = request.form.get('data_mapping').split("|")
    field_names = request.form.get('field_names').split("|")
    type = request.form.get('type')
    ignore_first = request.form.get('ignore_first')
    schema_name = request.form.get('schema_name')
    data_types = request.form.get('column_types').split("|")
    field_descriptions = request.form.get('field_descriptions').split("|")

    try:
        return makeResponse(payload=UploadManager.importData(repo_id, type, filename, original_filename, data_mapping, ignore_first, field_names, schema_name, data_types, field_descriptions), message="File imported")
    except UploadError as e:
        return makeResponse(error=e)

@upload_blueprint.route('/upload/importEventsForRepo/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def importEventsForRepo(repo_id):

    try:
        return makeResponse(payload=UploadManager.getImportEventsForRepo(repo_id),
                            message="")
    except Exception as e:
        return makeResponse(error=e)
