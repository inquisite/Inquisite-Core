import json

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from lib.managers.SchemaManager import SchemaManager
from lib.managers.PeopleManager import PeopleManager
from lib.utils.RequestHelpers import extractRepeatingParameterBlocksFromRequest, extractRepeatingParameterFromRequest, responseHandler
from lib.crossDomain import crossdomain
from lib.utils.RequestHelpers import makeResponse
from lib.exceptions.SettingsValidationError import SettingsValidationError

schema_blueprint = Blueprint('schema', __name__)

@schema_blueprint.route('/schema/getDataTypes', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getDataTypes():
    try:
        return makeResponse(payload=SchemaManager.getInfoForDataTypes())
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/getTypes/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getTypes(repo_id):
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        return makeResponse(payload=SchemaManager.getTypes(repo_id))
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/getType/<repo_id>/<schema_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getType(repo_id, schema_id):
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        return makeResponse(payload=SchemaManager.getType(repo_id, schema_id))
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/addType/<repo_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addType(repo_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        return makeResponse(message="Added type", payload=SchemaManager.addType(repo_id, name, code, description, extractRepeatingParameterBlocksFromRequest(request, 'fields')))
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/editType/<repo_id>/<type_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editType(repo_id, type_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        return makeResponse(message="Edited type", payload=SchemaManager.editType(repo_id, type_id, name, code, description, extractRepeatingParameterBlocksFromRequest(request, 'fields'), extractRepeatingParameterFromRequest(request, 'fieldsToDelete')))
    except SettingsValidationError as e:
        return makeResponse(error=e)
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/deleteType/<repo_id>/<type_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
#@jwt_required
def deleteType(repo_id, type_id):
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        return makeResponse(payload=SchemaManager.deleteType(repo_id, type_id), message="Deleted type")
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/addField/<repo_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addField(repo_id, typecode):
    name = request.form.get('name')
    code = request.form.get('code')
    fieldtype = request.form.get('type')
    description = request.form.get('description')
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        return makeResponse(payload=SchemaManager.addField(repo_id, typecode, name, code, fieldtype, description), message="Added field")
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/addData/<repo_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addData(repo_id, typecode):
    data = request.form.get('data')
    current_user = get_jwt_identity()
    if PeopleManager.checkRepoPermissions(current_user, repo_id) == False:
        return makeResponse(message="You do not have permissions to access this repository!")
    try:
        if SchemaManager.addDataToRepo(repo_id, typecode, json.loads(data)):
            return makeResponse(payload={"msg": "Added data to repository"})
        else:
            return makeResponse(payload={"msg": "No data to add"})
    except Exception as e:
        return makeResponse(error=e)
