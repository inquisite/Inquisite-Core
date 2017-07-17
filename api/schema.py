import json

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.models.schemaClass import Schema
from lib.utils.requestHelpers import extractRepeatingParameterBlocksFromRequest, extractRepeatingParameterFromRequest
from lib.responseHandler import response_handler
from lib.crossDomain import crossdomain

schema_blueprint = Blueprint('schema', __name__)

@schema_blueprint.route('/schema/getTypes/<repository_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getTypes(repository_id):
    return response_handler(Schema.getTypes(repository_id))

@schema_blueprint.route('/schema/addType/<repository_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addType(repository_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    return response_handler(Schema.addType(repository_id, name, code, description, extractRepeatingParameterBlocksFromRequest(request, 'fields')))

@schema_blueprint.route('/schema/editType/<repository_id>/<type_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editType(repository_id, type_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    return response_handler(Schema.editType(repository_id, type_id, name, code, description, extractRepeatingParameterBlocksFromRequest(request, 'fields'), extractRepeatingParameterFromRequest(request, 'fieldsToDelete')))

@schema_blueprint.route('/schema/deleteType/<repository_id>/<type_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
#@jwt_required
def deleteType(repository_id, type_id):
    return response_handler(Schema.deleteType(repository_id, type_id))

@schema_blueprint.route('/schema/addField/<repository_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addField(repository_id, typecode):
    name = request.form.get('name')
    code = request.form.get('code')
    fieldtype = request.form.get('type')
    description = request.form.get('description')

    return response_handler(Schema.addField(repository_id, typecode, name, code, fieldtype, description))

@schema_blueprint.route('/schema/addData/<repository_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addData(repository_id, typecode):
    data = request.form.get('data')

    return response_handler(Schema.addDataToRepo(repository_id, typecode, json.loads(data)))
