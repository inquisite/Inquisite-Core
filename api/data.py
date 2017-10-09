from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.managers.DataManager import DataManager
from lib.crossDomain import crossdomain
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError
from lib.utils.RequestHelpers import makeResponse

data_blueprint = Blueprint('data', __name__)

@data_blueprint.route('/data/getNode/<node_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getNode(node_id):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=DataManager.getByID(node_id))
    except FindError as e:
        return makeResponse(error=e)

@data_blueprint.route('/data/saveNode/<node_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def saveNode(node_id):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=DataManager.update(node_id, request.form))
    except SaveError as e:
        return makeResponse(error=e)

@data_blueprint.route('/data/getDataForType/<repo_id>/<type>', methods=['GET', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getDataForType(repo_id, type):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=DataManager.getDataForType(repo_id, type))
    except SaveError as e:
        return makeResponse(error=e)