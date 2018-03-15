import json

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.managers.ListManager import ListManager
from lib.utils.RequestHelpers import extractRepeatingParameterBlocksFromRequest, extractRepeatingParameterFromRequest, responseHandler
from lib.crossDomain import crossdomain
from lib.utils.RequestHelpers import makeResponse
from lib.exceptions.SettingsValidationError import SettingsValidationError

list_blueprint = Blueprint('list', __name__)

@list_blueprint.route('/list/getRepoLists/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoLists(repo_id):
    try:
        return makeResponse(payload=ListManager.getListsForRepo(repo_id))
    except Exception as e:
        return makeResponse(error=e)

@list_blueprint.route('/list/getListItems/<repo_id>/<list_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getListItems(repo_id, list_id):
    try:
        return makeResponse(payload=ListManager.getInfoForList(repo_id, list_id))
    except Exception as e:
        return makeResponse(error=e)

@list_blueprint.route('/list/editList/<repo_id>/<list_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editList(repo_id, list_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    items = extractRepeatingParameterBlocksFromRequest(request, 'items')
    delete_items = extractRepeatingParameterFromRequest(request, 'itemsToDelete')
    print items, delete_items
    try:
        return makeResponse(payload=ListManager.editList(repo_id, list_id, name, code, description, items, delete_items))
    except Exception as e:
        return makeResponse(error=e)

@list_blueprint.route('/list/addList/<repo_id>/<list_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addList(repo_id, list_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    items = extractRepeatingParameterBlocksFromRequest(request, 'items')

    try:
        return makeResponse(payload=ListManager.addList(repo_id, list_id, items))
    except Exception as e:
        return makeResponse(error=e)

@list_blueprint.route('/list/deleteList/<repo_id>/<list_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteList(repo_id, list_id):

    try:
        return makeResponse(payload=ListManager.deleteList(repo_id, list_id))
    except Exception as e:
        return makeResponse(error=e)
