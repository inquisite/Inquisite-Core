from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.managers.OrganizationManager import OrganizationManager
from lib.utils.Db import db
from lib.utils.RequestHelpers import responseHandler
from lib.crossDomain import crossdomain

organizations_blueprint = Blueprint('organizations', __name__)


# Organizations
@organizations_blueprint.route('/organizations', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def orgList():

    orgslist = OrganizationManager.getAll()
    ret = {
      'status_code': 200,
      'payload': {
        'orgs': orgslist
      }
    }

    return responseHandler(ret)


@organizations_blueprint.route('/organizations/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addOrg():
    name = request.form.get('name')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')

    ret = {
      'status_code': '',
      'payload': {
        'msg': '',
        'organization': ''
      }
    }


    if name is not None and location is not None and email is not None and url is not None and tagline is not None:

        result = db.run(
            "CREATE (o:Organization {name: {name}, location: {location}, email: {email}, url: {url}, tagline: {tagline}}) RETURN o.name AS name, o.location AS location, o.email AS email, o.url AS url, o.tagline AS tagline, ID(o) AS org_id", {"name": name, "location": location, "email": email, "url": url, "tagline": tagline})

        new_org = {}
        for org in result:
            new_org = {
                'org_id': org['org_id'],
                'name': org['name'],
                'location': org['location'],
                'email': org['email'],
                'url': org['url'],
                'tagline': org['tagline']
            }

        summary = result.consume()

        node_created = False
        if summary.counters.nodes_created == 1:
            node_created = True

        if node_created:
            ret['status_code'] = 200
            ret['payload']['msg'] = 'Organization Added'
            ret['payload']['organization'] = new_org

        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Problem adding Organization'

    else:
        ret['status_code'] = 422
        ret['payload']['msg'] = 'Missing required fields'

    return responseHandler(ret)


@organizations_blueprint.route('/organizations/<org_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getOrg(org_id):

    ret = {
      'status_code': '',
      'payload': {
        'msg': '',
        'organization': ''
      }
    }

    org = OrganizationManager.getInfo(int(org_id))
    if org:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success, organization found'
        ret['payload']['organization'] = org

    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'No organization found'

    return responseHandler(ret)

@organizations_blueprint.route('/organizations/<org_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editOrg(org_id):
    name = request.form.get('name')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')

    ret = {
      'status_code': '',
      'payload': {
        'msg': '',
        'org': ''
      }
    }

    update = []
    if name is not None:
        update.append("o.name = {name}")

    if location is not None:
        update.append("o.location = {location}")

    if email is not None:
        update.append("o.email = {email}")

    if url is not None:
        update.append("o.url = {url}")

    if tagline is not None:
        update.append("o.tagline = {tagline}")

    update_str = ''
    update_str = "%s" % ", ".join(map(str, update))

    if update_str:
        updated_org = {}
        result = db.run("MATCH (o:Organization) WHERE ID(o)={org_id} SET " + update_str +
                                " RETURN o.name AS name, o.location AS location, o.email AS email, o.url AS url, o.tagline AS tagline", {"org_id": org_id, "name": name, "location": location, "email": email, "url": url, "tagline": tagline})

        for o in result:
            updated_org['name'] = o['name']
            updated_org['location'] = o['location']
            updated_org['email'] = o['email']
            updated_org['url'] = o['url']
            updated_org['tagline'] = o['tagline']

        if updated_org:
            ret['status_code'] = 200
            ret['payload']['msg'] = 'Organization updated'
            ret['payload']['org'] = updated_org
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Problem updating Organization'
            
    else:
        ret['status_code'] = 422 
        ret['payload']['msg'] = 'Nothing to update'

    return responseHandler(ret)


@organizations_blueprint.route('/organizations/<org_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteOrg(org_id):

    ret = {
      'status_code': '',
      'payload': {
        'msg': ''
      }
    }

    node_delete = OrganizationManager.delete(int(org_id))
    if node_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Organization deleted'
    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'Problem deleting Organization'

    return responseHandler(ret)

@organizations_blueprint.route('/organizations/<org_id>/repos', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getOrgRepos(org_id):

    ret = {
      'status_code': '',
      'payload': {
        'msg': '',
        'repos': ''
      }
    }

    repos = OrganizationManager.getRepos(int(org_id))
    if repos:
        ret['status_code'] = 200
        ret['payload']['repos'] = repos
    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'Problem getting repos for Organization'

    return responseHandler(ret)

@organizations_blueprint.route('/organizations/<org_id>/repos/<repo_id>/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoToOrg(org_id, repo_id):

    ret = {
      'status_code': '',
      'payload': {
        'msg': ''
      }
    }

    rel_created = OrganizationManager.addRepository(int(org_id), int(repo_id))
    if rel_created:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Added Repo to Org'
    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'There was a problem adding Rep to Org'

    return responseHandler(ret)

@organizations_blueprint.route('/organizations/<org_id>/repos/<repo_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoFromOrg(org_id, repo_id):

    ret = {
      'status_code': '',
      'payload': {
        'msg': ''
      }
    }
 
    rel_deleted = OrganizationManager.removeRepository(int(org_id), int(repo_id))
    if rel_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Repo removed from Org'
    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'There was a problem, Repo was not removed from Org'

    return responseHandler(ret)

@organizations_blueprint.route('/organizations/<org_id>/add_person/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addPersonToOrg(org_id, person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem adding person to organization'
      }
    }

    rel_created = OrganizationManager.addPerson(int(org_id), int(person_id))
    if rel_created:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Person was added to Org'
    
    return responseHandler(ret)

@organizations_blueprint.route('/organizations/<org_id>/remove_person/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removePersonFromOrg(org_id, person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem removing Person from Organization'
      }
    }

    removed = OrganizationManager.removePerson(int(org_id), int(person_id))
    if removed:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Person was successfully removed from Org'

    return responseHandler(ret)


@organizations_blueprint.route('/organizations/<org_id>/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getOrgPeople(org_id):

    org_people = OrganizationManager.getPeople(int(org_id))

    ret['status_code'] = 200
    ret['payload']['people'] = org_people

    return responseHandler(ret)
