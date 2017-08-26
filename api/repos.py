import json
import os
import re

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_raw_jwt
from lib.managers.RepoManager import RepoManager
from werkzeug.utils import secure_filename

from lib.dataReaders.CSVData import CsvHandler
from lib.dataReaders.JSONData import JSONHandler
from lib.dataReaders.XLSData import XlsHandler
from lib.managers.SchemaManager import SchemaManager
from lib.utils.db import db
from lib.utils.requestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.utils.utilityHelpers import flatten_json
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.ValidationError import ValidationError

repositories_blueprint = Blueprint('repositories', __name__)

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/uploads"
ALLOWED_EXTENSIONS = set(['xls', 'xlsx', 'csv', 'json'])

# File Upload
def allowed_file(filename):
  return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


# Repositories
@repositories_blueprint.route('/repositories', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def repoList():
    try:
        return makeResponse(payload=RepoManager.getAll())
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepo(repo_id):
    try:
        return makeResponse(payload=RepoManager.getInfo(int(repo_id)))
    except FindError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepo():
    url = request.form.get('url')
    name = request.form.get('name')
    readme = request.form.get('readme')

    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']
    ident_str = "p.email = {identity}"

    try:
        return makeResponse(payload=RepoManager.create(url, name, readme, identity, ident_str), message="Created repository")
    except ValidationError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/<repo_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editRepo(repo_id):
    url = request.form.get('url')
    name = request.form.get('name')
    readme = request.form.get('readme')

    try:
        return makeResponse(payload=RepoManager.edit(repo_id, name, url, readme), message="Edited repository")
    except FindError as e:
        return makeResponse(error=e)
    except ValidationError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepo():
    repo_id = int(request.form.get('repo_id'))
    try:
        RepoManager.delete(repo_id)
        return makeResponse(payload={"repo_id": repo_id}, message="Repository deleted")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)


@repositories_blueprint.route('/repositories/set_owner', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setRepoOwner(repo_id):
    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']
    ident_str = "p.email = {identity}"

    try:
        RepoManager.setOwner(int(repo_id), identity, ident_str)
        return makeResponse(payload={}, message="Set repository owner")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)


@repositories_blueprint.route('/repositories/<repo_id>/owner', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoOwner(repo_id):
    try:
        owner = RepoManager.getOwner(int(repo_id))
        return makeResponse(payload=owner)
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/<repo_id>/remove_owner/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepoOwner(repo_id, person_id):
    try:
        rel_deleted = RepoManager.deleteOwner(int(repo_id), int(person_id))
        return makeResponse(payload={}, message="Deleted owner")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoInfo(repo_id):
    try:
        repo = RepoManager.getInfo(int(repo_id))
        return makeResponse(payload=repo)
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/add_collaborator', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoCollab():
    repo_id = int(request.form.get('repo_id'))
    person_id = int(request.form.get('person_id'))
    access = request.form.get('access')

    try:
        RepoManager.addCollaborator(repo_id, person_id, access)
        return makeResponse(message="Collaborator added")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)


@repositories_blueprint.route('/repositories/<repo_id>/collaborators', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoCollabs(repo_id):
    try:
        return makeResponse(payload=RepoManager.getCollaborators(int(repo_id)))
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/users', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoUsers():
    repo_id = int(request.form.get('repo_id'))

    try:
        return makeResponse(payload=RepoManager.getUsers(repo_id))
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/remove_collaborator', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoCollab():
    repo_id = request.form.get('repo_id')
    person_id = request.form.get('person_id')

    try:
        RepoManager.removeCollaborator(int(repo_id), int(person_id))
        return makeResponse(message="Collaborator removed")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)


@repositories_blueprint.route('/repositories/<repo_id>/add_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoFollower(repo_id, person_id):
    try:
        RepoManager.addFollower(int(repo_id), int(person_id))
        return makeResponse(message="Collaborator added")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)


@repositories_blueprint.route('/repositories/<repo_id>/followers', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoFollowers(repo_id):
    try:
        return makeResponse(payload=RepoManager.getFollowers(int(repo_id)))
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/<repo_id>/remove_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoFollower(repo_id, person_id):
    try:
        RepoManager.removeFollower(int(repo_id), int(person_id))
        return makeResponse(message="Follower removed")
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/data', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoData():
  repo_id = int(request.form.get('repo_id'))

  try:
      return makeResponse(payload=RepoManager.getData(repo_id))
  except FindError as e:
      return makeResponse(error=e)
  except DbError as e:
      return makeResponse(error=e)

@repositories_blueprint.route('/repositories/upload', methods=['PUT', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def uploadData():
    repo_id = int(request.form.get('repo_id'))

    if request.files:
        for f in request.files:
            print(f)
    else:
        pass

    if 'repo_file' not in request.files:
        return makeResponse(message="File not found")


    input_file = request.files['repo_file']

    file_data = []

    # sanity check
    if input_file and allowed_file(input_file.filename):

        filename = secure_filename(input_file.filename)

        upload_file = os.path.join(UPLOAD_FOLDER, filename)
        input_file.save(upload_file)

        basename = os.path.basename(upload_file)

        # Detect File Type
        filename, file_extension = os.path.splitext(upload_file)

        # ... dynamically set this per data node
        fieldnames = []
        nestednames = []
        rowcount = 0
        typecode = "text"

        original_filename, original_extension = os.path.splitext(os.path.basename(input_file.filename))
        datatype = re.sub(r'[^A-Za-z0-9_\-]+', '_', original_filename).strip().lower()

        if ".csv" == file_extension:

            # Get some contents from the File
            csvhandler = CsvHandler(upload_file)
            file_data = csvhandler.read_file()
            rowcount = len(file_data)
            fieldnames = json.loads(file_data[0]).keys()

            SchemaManager.createDataTypeFromFields(repo_id, datatype.lower(), fieldnames)

            # Create nodes
            for row in file_data:
                SchemaManager.addDataToRepo(repo_id, datatype, json.loads(row))

        if ".json" == file_extension:

            jsonhandler = JSONHandler(upload_file)
            file_data = jsonhandler.read_file()

            if type(file_data) == dict:
                fieldnames = file_data.keys()
                rowcount = len(file_data)

                SchemaManager.createDataTypeFromFields(repo_id, datatype, fieldnames)

                if len(fieldnames) <= 1:
                    nestednames = file_data[fieldnames[0]][0].keys()
                    rowcount = len(file_data[fieldnames[0]])

                    for item in file_data[fieldnames[0]]:
                        # Flatten our nested JSON for insertion into Neo4j
                        # TODO: do you use pandas json_normalize to turn into dataframe?
                        flat = flatten_json(item)
                        SchemaManager.addDataToRepo(repo_id, datatype, flat)

                else:
                    for item in file_data:
                        flat = flatten_json(item)
                        # TODO: consider pandas json_normailize to turn into dataframe?

                        SchemaManager.createDataTypeFromFields(repo_id, datatype.lower(), fieldnames)

                        SchemaManager.addDataToRepo(repo_id, datatype, flat)

        if ".xlsx" == file_extension or ".xls" == file_extension:

            # Get some contents from the File
            xhandler = XlsHandler(upload_file)
            file_data = xhandler.read_file()
            rowcount = len(file_data)
            fieldnames = file_data[0]

            for item in file_data:
                # Assumes that row 1 is column headers
                # TODO: improve this assumption? -- Parse data, get max row count, look for first row with that row count?
                if item != fieldnames:
                    SchemaManager.createDataTypeFromFields(repo_id, datatype, fieldnames)

                    # Create Dict of key:values by combining fieldnames with row into a dict
                    row = dict(zip(fieldnames, item))
                    SchemaManager.addDataToRepo(repo_id, datatype, row)

    # Send first ten rows as teaser
    if file_data:
        payload = {
            "data": [],
            "fieldnames": fieldnames,
            "nestednames": nestednames,
            "row_count": rowcount
        }
    else:
        payload = {}

    return makeResponse(payload=payload)