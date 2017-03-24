import os
import json
import requests
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_raw_jwt
from werkzeug.security import safe_str_cmp
from werkzeug.utils import secure_filename
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth
from inquisite.db import db
from neo4j.v1 import ResultError
from lib.schema import addType, addField, addDataToRepo 

from pandas.io.json import json_normalize

from response_handler import response_handler
from xlsdata import XlsHandler
from csvdata import CsvHandler
from jsondata import JSONHandler

repositories_blueprint = Blueprint('repositories', __name__)

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = UPLOAD_FOLDER.replace('inquisite', 'uploads')
ALLOWED_EXTENSIONS = set(['xls', 'xlsx', 'csv', 'json'])

# File Upload
def allowed_file(filename):
  return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# Flatten JSON
def flatten_json(y):
  out = {}
 
  def flatten(x, name=''):
    if type(x) is dict:
      for a in x:
        flatten(x[a], name + a + '_')
    elif type(x) is list:
      i = 0
      for a in x:
        flatten(a, name + str(i) + '_')
        i += 1
    else:
      out[name[:-1]] = x

  flatten(y)
  return out

# Repositories
@repositories_blueprint.route('/repositories', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def repoList():

    repos = []
    result = db.run("MATCH (n:Repository) RETURN n.url AS url, n.name AS name, n.readme AS readme")
    for r in result:
        repos.append({
            "name": r['name'],
            "url": r['url'],
            "readme": r['readme']
        })

    ret = {
      'status_code': 200,
      'payload': {
        'msg': 'Success',
        'repos': repos
      }
    }

    return response_handler(ret)

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

    repo = {}
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} RETURN n.url AS url, n.name AS name, n.readme AS readme", {"repo_id": repo_id})
    for r in result:
        repo['url'] = r['url']
        repo['name'] = r['name']
        repo['readme'] = r['readme']

    if repo:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['repo'] = repo

    return response_handler(ret)

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


    ret = {
      'status_code': 422,
      'payload': {
        'msg': 'Required fields are missing',
        'repo': {}
      } 
    }

    print "Repo Name"
    print name

    print "Repo URL"
    print url

    print "Repo README"
    print readme

    if url is not None and name is not None and readme is not None:
        try:
           db.run("MATCH (n:Repository {name: {name}}) RETURN n", {"name": name}).peek()

           ret['status_code'] = 400
           ret['payload']['msg'] = 'Repository with name already exists'

        except ResultError as e:
            ts = time.time()
            created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            new_repo = {}
            result = db.run("CREATE (n:Repository {url: {url}, name: {name}, readme: {readme}, created_on: {created_on}}) RETURN n.url AS url, n.name AS name, n.readme AS readme, ID(n) AS repo_id", {"url": url, "name": name, "readme": readme, "created_on": created_on})

            for r in result:
                new_repo['repo_id'] = r['repo_id']
                new_repo['url'] = r['url']
                new_repo['name'] = r['name']
                new_repo['readme'] = r['readme']

            node_created = False
            summary = result.consume()
            if summary.counters.nodes_created >= 1:
                node_created = True

            if node_created:

                # CHEAP HACK - Dump SET OWNER GUTS HERE
                # TODO: -- Make me pretty
                result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE p.email={identity} MERGE (p)<-[:OWNED_BY]->(n)", 
                  {"repo_id": new_repo['repo_id'], "identity": identity})
                summary = result.consume()

                rel_created = False
                if summary.counters.relationships_created >= 1:
                  rel_created = True

                  if rel_created:

                    print "Node Created AND OWNED BY Relationship Created"

                    ret['status_code'] = 200
                    ret['payload']['msg'] = 'Created Repo'
                    ret['payload']['repo'] = new_repo

            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Problem creating repo'

    return response_handler(ret)

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
                                " RETURN n.name AS name, n.url AS url, n.readme AS readme", {"repo_id": repo_id, "name": name, "url": url, "readme": readme})

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
            ret['payload']['msg'] = 'Problem updating Repo'

    return response_handler(ret)


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

    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n", {"repo_id": int(repo_id)})
    summary = result.consume()

    node_deleted = False
    if summary.counters.nodes_deleted >= 1:
        node_deleted = True

    if node_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repo deleted successfully'

    return response_handler(ret)


@repositories_blueprint.route('/repositories/set_owner', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setRepoOwner(repo_id):

    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem, no owner set'
      }
    }

    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)<-[:OWNED_BY]->(n)", {"repo_id": repo_id, "person_id": person_id})
    summary = result.consume()

    rel_created = False
    if summary.counters.relationships_created >= 1:
        rel_created = True

    if rel_created:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repository owner set successfully'

    return response_handler(ret)


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

    owner = {}
    result = db.run("MATCH (n)<-[:OWNED_BY]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline", {"repo_id": repo_id})
    for r in result:
        owner['name'] = r['name']
        owner['location'] = r['location']
        owner['email'] = r['email']
        owner['url'] = r['url']
        owner['tagline'] = r['tagline']

    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['owner'] = owner

    return response_handler(ret)


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

    result = db.run(
        "START p=node(*) MATCH (p)-[rel:OWNED_BY]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel", {"person_id": person_id, "repo_id": repo_id})
    summary = result.consume()

    rel_deleted = False
    if summary.counters.relationships_deleted >= 1:
        rel_deleted = True

    if rel_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repo owner removed successfully'

    return response_handler(ret)


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

    repo = {}
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} RETURN n.name AS name, n.url AS url, n.readme AS readme", {"repo_id": repo_id})
    for r in result:
        repo['name'] = r['name']
        repo['url'] = r['url']
        repo['readme'] = r['readme']

    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['repo'] = repo

    return response_handler(ret)


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

    print "repo_id: " + str(repo_id) 
    print "person id:" + str(person_id)
    

    if repo_id is not None and person_id is not None:

      print " we have valid repo id and person"
      print "repo_id: " + str(repo_id) 
      print "person id:" + str(person_id)

      result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:COLLABORATES_WITH]->(n)", 
        {"repo_id": int(repo_id), "person_id": int(person_id)})

      summary = result.consume()

      rel_created = False
      if summary.counters.relationships_created >= 1:
        rel_created = True

      if rel_created:
          ret['status_code'] = 200
          ret['payload']['msg'] = 'Collaborator Added'

    return response_handler(ret)


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

    people = []
    result = db.run("MATCH (n)<-[:COLLABORATES_WITH]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline", {"repo_id": repo_id})

    for p in result:
        people.append({
            "name": p['name'],
            "email": p['email'],
            "url": p['url'],
            "location": p['location'],
            "tagline": p['tagline']
        })

    if people:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['collaborators'] = people

    return response_handler(ret)

@repositories_blueprint.route('/repositories/users', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoUsers():

    repo_id = request.form.get('repository_id')

    ret = { 
      'status_code': 200,
      'payload': {
        'msg': 'There was a problem returning users',
        'users': {}
      }
    }

    users = []
    if repo_id is not None:
      result = db.run("MATCH (n)<-[rel:COLLABORATES_WITH|OWNED_BY]-(p) WHERE ID(n)={repo_id} RETURN type(rel) AS role, p.name AS name, ID(p) AS id", 
        {"repo_id": int(repo_id)})

      for p in result:

        user_role = ""
        if p['role'] == "COLLABORATES_WITH":
          user_role = "collaborator"
        if p['role'] == "OWNED_BY":
          user_role = "owner"

        users.append({
          "id": p['id'],
          "name": p['name'],
          "role": user_role
        })

      if users:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['users'] = users

    return response_handler(ret)

@repositories_blueprint.route('/repositories/<repo_id>/remove_collaborator/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoCollab(repo_id, person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Problem removing collaborator'
      }
    }

    result = db.run(
        "START p=node(*) MATCH (p)-[rel:COLLABORATES_WITH]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel", {"person_id": person_id, "repo_id": repo_id})
    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Collaborator removed'

    return response_handler(ret)


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

    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:FOLLOWS]->(n)", {"repo_id": repo_id, "person_id": person_id})
    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Follower added successfully'

    return response_handler(ret)


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

    people = []
    result = db.run("MATCH (n)<-[:FOLLOWS]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline", {"repo_id": repo_id})

    for p in result:
        people.append({
            "name": p['name'],
            "email": p['email'],
            "url": p['url'],
            "location": p['location'],
            "tagline": p['tagline']
        })

    if people:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['followers'] = people

    return response_handler(ret)


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

    result = db.run(
        "START p=node(*) MATCH (p)-[rel:FOLLOWS]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel", {"person_id": person_id, "repo_id": repo_id})
    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Follower Removed'

    return response_handler(ret)

@repositories_blueprint.route('/repositories/upload', methods=['PUT', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def uploadData():

    print "You're in uploadData"

    repo_id = request.form.get('repo_id')

    print "Uploaded Data will be added to REPO: " + str(repo_id)

    ret = {
      'status_code': 200,
      'payload': {
        'msg': 'Success',
        'data': ''
      }
    }

    if request.files:
      print "there are files in request"
      for f in request.files:
        print f
    else:
      print "no files in request"


    if 'repo_file' not in request.files:
      print "We couldn't find it"
      ret['status_code'] = 400
      ret['payload']['msg'] = 'File not found'


    if 'repo_file' not in request.files:
      ret['status_code'] = 400
      ret['payload']['msg'] = 'Upload File not Found'

    input_file = request.files['repo_file']
    
    file_data = []

    # sanity check
    if input_file and allowed_file(input_file.filename):

      print "File is an allowed type"

      filename = secure_filename(input_file.filename)

      upload_file = os.path.join(UPLOAD_FOLDER, filename)
      input_file.save( upload_file )

      basename = os.path.basename( upload_file )

      # Detect File Type
      filename, file_extension = os.path.splitext(upload_file)

      print "file extension: "
      print file_extension

      # ... dynamically set this per data node 
      fieldnames = []
      nestednames = []
      rowcount = 0
      typecode = "text"

      if ".csv" == file_extension:

        # Get some contents from the File
        csvhandler = CsvHandler(upload_file)
        file_data  = csvhandler.read_file()
        rowcount = len(file_data)
        fieldnames = json.loads(file_data[0]).keys()

        # Create nodes
        for row in file_data:
          print "Row:"
          print row
          
          addDataToRepo(repo_id, typecode, json.loads(row))

      if ".json" == file_extension:
     
        jsonhandler = JSONHandler(upload_file)
        file_data = jsonhandler.read_file()

        if type( file_data ) == dict:
          fieldnames = file_data.keys()
          rowcount = len(file_data)
     
          if len( fieldnames ) <= 1:
            nestednames = file_data[fieldnames[0]][0].keys()
            rowcount = len( file_data[fieldnames[0]] )

            for item in file_data[fieldnames[0]]:

              # Flatten our nested JSON for insertion into Neo4j
              # TODO: do you use pandas json_normalize to turn into dataframe?
              flat = flatten_json(item)
              addDataToRepo(repo_id, typecode, flat)

          else:
            for item in file_data:
              flat = flatten_json(item)
              # TODO: consider pandas json_normailize to turn into dataframe?
              addDataToRepo(repo_id, typecode, flat)

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
          
            # Create Dict of key:values by combining fieldnames with row into a dict
            row = dict(zip( fieldnames, item ))
            addDataToRepo(repo_id, typecode, row)


      
    # Send first ten rows as teaser
    if file_data:
      ret['payload']['data'] = [] #file_data[:11]
      ret['payload']['fieldnames'] = fieldnames 
      ret['payload']['nestednames'] = nestednames
      ret['payload']['row_count'] = rowcount
    else: 
      ret['payload']['data'] = []
    return response_handler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/add_data_node', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoData(repo_id):
    result = db.run()


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

  print "REPO ID: " + str(repo_id)

  if repo_id is not None:
    result = db.run("MATCH (r:Repository)<-[rel:PART_OF]-(n) WHERE ID(r)={repo_id} RETURN n LIMIT 2", {"repo_id": int(repo_id)})

    nodes = []
    for data in result:
      print "Gut CHECK DATA"

      print data.items()[0][1].properties
      nodes.append(data.items()[0][1].properties)

    ret['payload']['data'] = nodes

  return response_handler(ret)


@repositories_blueprint.route('/repositories/<repo_id>/set_entry_point', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setEntryPoint(repo_id):
    result = db.run()
