import json

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.managers.SchemaManager import SchemaManager
from lib.utils.RequestHelpers import extractRepeatingParameterBlocksFromRequest, extractRepeatingParameterFromRequest, responseHandler
from lib.crossDomain import crossdomain
from lib.utils.RequestHelpers import makeResponse

schema_blueprint = Blueprint('schema', __name__)

@schema_blueprint.route('/schema/getTypes/<repository_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getTypes(repository_id):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=SchemaManager.getTypes(repository_id))
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/addType/<repository_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addType(repository_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    # TODO: check that user has access to this data
    try:
        return makeResponse(message="Added type", payload=SchemaManager.addType(repository_id, name, code, description, extractRepeatingParameterBlocksFromRequest(request, 'fields')))
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/editType/<repository_id>/<type_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editType(repository_id, type_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    x = SchemaManager()
    print "GOT "
    print x.get
    # TODO: check that user has access to this data
    try:
        return makeResponse(message="Edited type", payload=SchemaManager.editType(repository_id, type_id, name, code, description, extractRepeatingParameterBlocksFromRequest(request, 'fields'), extractRepeatingParameterFromRequest(request, 'fieldsToDelete')))
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/deleteType/<repository_id>/<type_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
#@jwt_required
def deleteType(repository_id, type_id):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload={}, message="Deleted type")
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/addField/<repository_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addField(repository_id, typecode):
    name = request.form.get('name')
    code = request.form.get('code')
    fieldtype = request.form.get('type')
    description = request.form.get('description')

    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=SchemaManager.addField(repository_id, typecode, name, code, fieldtype, description), message="Added field")
    except Exception as e:
        return makeResponse(error=e)

@schema_blueprint.route('/schema/addData/<repository_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addData(repository_id, typecode):
    data = request.form.get('data')

    # TODO: check that user has access to this data
    try:
        if SchemaManager.addDataToRepo(repository_id, typecode, json.loads(data)):
            return makeResponse(payload={"msg": "Added data to repository"})
        else:
            return makeResponse(payload={"msg": "No data to add"})
    except Exception as e:
        return makeResponse(error=e)