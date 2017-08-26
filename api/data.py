from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.managers.dataManager import Data
from lib.utils.requestHelpers import responseHandler
from lib.crossDomain import crossdomain
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError
from lib.utils.requestHelpers import makeResponse

data_blueprint = Blueprint('data', __name__)

@data_blueprint.route('/data/getNode/<node_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getNode(node_id):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=Data.getNode(node_id))
    except FindError as e:
        return makeResponse(error=e)

@data_blueprint.route('/data/saveNode/<node_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def saveNode(node_id):
    # TODO: check that user has access to this data
    try:
        return makeResponse(payload=Data.saveNode(node_id, request.form))
    except SaveError as e:
        return makeResponse(error=e)