from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_raw_jwt
from lib.managers.RepoManager import RepoManager
from lib.utils.RequestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.ValidationError import ValidationError

repositories_blueprint = Blueprint('repositories', __name__)

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
    license = request.form.get('license')
    published = request.form.get('published')

    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']
    ident_str = "p.email = {identity}"

    try:
        return makeResponse(payload=RepoManager.create(url, name, readme, license, published, identity, ident_str), message="Created repository")
    except ValidationError as e:
        return makeResponse(error=e)

@repositories_blueprint.route('/repositories/<repo_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editRepo(repo_id):
    url = request.form.get('url')
    name = request.form.get('name')
    readme = request.form.get('readme')
    license = request.form.get('license')
    published = request.form.get('published')

    try:
        return makeResponse(payload=RepoManager.edit(repo_id, name, url, readme, license, published), message="Edited repository")
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