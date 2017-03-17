import os
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

from response_handler import response_handler
from xlsdata import XlsHandler

repositories_blueprint = Blueprint('repositories', __name__)

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = UPLOAD_FOLDER.replace('inquisite', 'uploads')
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])

# File Upload
def allowed_file(filename):
  return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


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

    repo_id = request.form.get('repo_id')

    ret = { 
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem returning users',
        'users': {}
      }
    }

    users = []
    if repo_id is not None:
      result = db.run("MATCH (n)<-[:COLLABORATES_WITH|OWNED_BY]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, ID(p) AS id", {"repo_id": int(repo_id)})

      for p in result:
        users.append({
          "id": p['id'],
          "name": p['name']
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
    
    # sanity check
    if input_file and allowed_file(input_file.filename):
      filename = secure_filename(input_file.filename)

      upload_file = os.path.join(UPLOAD_FOLDER, filename)
      input_file.save( upload_file )

      basename = os.path.basename( upload_file )

    # Get some contents from the File
    xhandler = XlsHandler(upload_file)
    file_data = xhandler.read_file() 
 
    ret['payload']['data'] = file_data

    # TODO Add data node
    # TODO Add relationshop between data node and Repo

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


@repositories_blueprint.route('/repositories/<repo_id>/get_all_data', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoData(repo_id):
    result = db.run()


@repositories_blueprint.route('/repositories/<repo_id>/set_entry_point', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setEntryPoint(repo_id):
    result = db.run()
