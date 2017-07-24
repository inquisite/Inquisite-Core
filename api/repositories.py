import json
import os
import re

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_raw_jwt
from lib.models.repositoriesClass import Repositories
from werkzeug.utils import secure_filename

from lib.dataReaders.csvdata import CsvHandler
from lib.dataReaders.jsondata import JSONHandler
from lib.dataReaders.xlsdata import XlsHandler
from lib.models.schemaClass import Schema
from lib.utils.db import db
from lib.utils.requestHelpers import responseHandler
from lib.crossDomain import crossdomain
from lib.utils.utilityHelpers import flatten_json

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

    repos = Repositories.getAll() 
    ret = {
      'status_code': 200,
      'payload': {
        'msg': 'Success',
        'repos': repos
      }
    }

    return responseHandler(ret)

@repositories_blueprint.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepo(repo_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'No repository found',
        'repo': {}
      }
    }

    repo = Repositories.getInfo( int(repo_id) )
   
    if repo:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['repo'] = repo

    return responseHandler(ret)

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

    ret = {
      'status_code': 422,
      'payload': {
        'msg': 'Required fields are missing',
        'repo': {}
      } 
    }
    
    if url is not None and name is not None and readme is not None:
        is_valid = Repositories.nameCheck(name)
        if is_valid:
          new_repo = Repositories.create(url, name, readme, identity, ident_str)

          if new_repo:
            ret['status_code'] = 200
            ret['payload']['msg'] = 'Created Repo'
            ret['payload']['repo'] = new_repo
          else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Problem creating repo'
        else:
          ret['status_code'] = 400
          ret['payload']['msg'] = 'Repository with name already exists'
            
    return responseHandler(ret)

@repositories_blueprint.route('/repositories/<repo_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editRepo(repo_id):
    url = request.form.get('url')
    name = request.form.get('name')
    readme = request.form.get('readme')

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Nothing to update'
      }
    }

    update = []
    if name is not None:
        update.append("n.name = {name}")

    if url is not None:
        update.append("n.url = {url}")

    if readme is not None:
        update.append("n.readme = {readme}")

    update_str = "%s" % ", ".join(map(str, update))

    if update_str:
        result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} SET " + update_str +
                                " RETURN n.name AS name, n.url AS url, n.readme AS readme", {"repo_id": int(repo_id), "name": name, "url": url, "readme": readme})

        updated_repo = {}
        for r in result:
            updated_repo['name'] = r['name']
            updated_repo['url'] = r['url']
            updated_repo['readme'] = r['readme']

        node_updated = False
        summary = result.consume()
        if summary.counters.properties_set >= 1:
            node_updated = True

        if node_updated:
            ret['status_code'] = 200
            ret['payload']['msg'] = 'Repository updated'
            ret['payload']['repo'] = updated_repo
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Problem updating Repo ' + str(repo_id)

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepo():

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Problem deleting repo'
      }
    }

    repo_id = request.form.get('repo_id')
    node_deleted = Repositories.delete( int(repo_id) )
    
    if node_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repo deleted successfully'
        ret['payload']['repo_id'] = repo_id

    return responseHandler(ret)


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

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem, no owner set'
      }
    }

    rel_created = Repositories.setOwner( int(repo_id), identity, ident_str )
    if rel_created:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repository owner set successfully'

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/owner', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoOwner(repo_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Could not retrieve owner',
        'owner': {}
      }
    }

    owner = Repositories.getOwner( int(repo_id) )
    if owner:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['owner'] = owner

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/remove_owner/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepoOwner(repo_id, person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem, Repo owner was not removed'
      }
    }

    rel_deleted = Repositories.deleteOwner( int(repo_id), int(person_id) )
    if rel_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repo owner removed successfully'

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoInfo(repo_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Could not return repo info',
        'repo': {}
      }
    }

    repo = Repositories.getInfo( int(repo_id) )
    if repo:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['repo'] = repo

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/add_collaborator', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoCollab():

    repo_id = request.form.get('repo_id')
    person_id = request.form.get('person_id')

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Problem adding Collaborator'
      }
    }

    if repo_id is not None and person_id is not None:
      rel_created = Repositories.addCollaborator(int(repo_id), int(person_id))
      if rel_created:
          ret['status_code'] = 200
          ret['payload']['msg'] = 'Collaborator Added'

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/collaborators', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoCollabs(repo_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem returning collaborators',
        'collaborators': {}
      }
    }

    people = Repositories.getCollaborators( int(repo_id) )
    if people:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['collaborators'] = people

    return responseHandler(ret)

@repositories_blueprint.route('/repositories/users', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoUsers():

    repo_id = request.form.get('repo_id')

    ret = { 
      'status_code': 200,
      'payload': {
        'msg': 'There was a problem returning users',
        'users': {}
      }
    }

    if repo_id is not None:
      users = Repositories.getUsers( int(repo_id) )

      if users:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['users'] = users

    return responseHandler(ret)

@repositories_blueprint.route('/repositories/remove_collaborator', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoCollab():
    repo_id = request.form.get('repo_id')
    person_id = request.form.get('person_id')

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Problem removing collaborator'
      }
    }

    removed = Repositories.removeCollaborator( int(repo_id), int(person_id) )
    if removed:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Collaborator removed'

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/add_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoFollower(repo_id, person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem adding follower'
      }
    }

    add_follower = Repositories.addFollower( int(repo_id), int(person_id) )
    if add_follower:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Follower added successfully'

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/followers', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoFollowers(repo_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem returning followers',
        'followers': {}
      }
    }

    people = Repositories.getFollowers( int(repo_id) )
    if people:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['followers'] = people

    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/remove_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoFollower(repo_id, person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Problem removing follower'
      }
    }

    remove_follower = Repositories.removeFollower( int(repo_id), int(person_id) )
    if remove_follower:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Follower Removed'

    return responseHandler(ret)

@repositories_blueprint.route('/repositories/upload', methods=['PUT', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def uploadData():
    repo_id = request.form.get('repo_id')

    ret = {
      'status_code': 200,
      'payload': {
        'msg': 'Success',
        'data': ''
      }
    }

    if request.files:
      for f in request.files:
        print(f)
    else:
      pass


    if 'repo_file' not in request.files:
      ret['status_code'] = 400
      ret['payload']['msg'] = 'File not found'


    if 'repo_file' not in request.files:
      ret['status_code'] = 400
      ret['payload']['msg'] = 'Upload File not Found'

    input_file = request.files['repo_file']
    
    file_data = []

    # sanity check
    if input_file and allowed_file(input_file.filename):

      filename = secure_filename(input_file.filename)

      upload_file = os.path.join(UPLOAD_FOLDER, filename)
      input_file.save( upload_file )

      basename = os.path.basename( upload_file )

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
        file_data  = csvhandler.read_file()
        rowcount = len(file_data)
        fieldnames = json.loads(file_data[0]).keys()

        Schema.createDataTypeFromFields(repo_id, datatype.lower(), fieldnames)

        # Create nodes
        for row in file_data:
          Schema.addDataToRepo(repo_id, datatype, json.loads(row))

      if ".json" == file_extension:
     
        jsonhandler = JSONHandler(upload_file)
        file_data = jsonhandler.read_file()

        if type( file_data ) == dict:
          fieldnames = file_data.keys()
          rowcount = len(file_data)

          Schema.createDataTypeFromFields(repo_id, datatype, fieldnames)
     
          if len( fieldnames ) <= 1:
            nestednames = file_data[fieldnames[0]][0].keys()
            rowcount = len( file_data[fieldnames[0]] )

            for item in file_data[fieldnames[0]]:

              # Flatten our nested JSON for insertion into Neo4j
              # TODO: do you use pandas json_normalize to turn into dataframe?
              flat = flatten_json(item)
              Schema.addDataToRepo(repo_id, datatype, flat)

          else:
            for item in file_data:
              flat = flatten_json(item)
              # TODO: consider pandas json_normailize to turn into dataframe?

              Schema.createDataTypeFromFields(repo_id, datatype.lower(), fieldnames)

              Schema.addDataToRepo(repo_id, datatype, flat)

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
            Schema.createDataTypeFromFields(repo_id, datatype, fieldnames)

            # Create Dict of key:values by combining fieldnames with row into a dict
            row = dict(zip( fieldnames, item ))
            Schema.addDataToRepo(repo_id, datatype, row)


      
    # Send first ten rows as teaser
    if file_data:
      ret['payload']['data'] = [] #file_data[:11]
      ret['payload']['fieldnames'] = fieldnames 
      ret['payload']['nestednames'] = nestednames
      ret['payload']['row_count'] = rowcount
    else: 
      ret['payload']['data'] = []
    return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/query', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def queryRepo(repo_id):
    result = db.run()


@repositories_blueprint.route('/repositories/data', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoData():
  repo_id = request.form.get('repo_id')

  ret = {
    'status_code': 200,
    'payload': {
      'msg': 'Success',
      'data': ''
    }
  }

  if repo_id is not None:

    nodes = Repositories.getData( int(repo_id) )
    ret['payload']['data'] = nodes

  return responseHandler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/set_entry_point', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setEntryPoint(repo_id):
    result = db.run()
