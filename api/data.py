from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.models.dataClass import Data
from lib.responseHandler import response_handler
from lib.crossDomain import crossdomain

data_blueprint = Blueprint('data', __name__)

@data_blueprint.route('/data/getNode/<node_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getNode(node_id):
    # TODO: check that user has access to this data

    return response_handler(Data.getNode(node_id))

@data_blueprint.route('/data/saveNode/<node_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def saveNode(node_id):
    # TODO: check that user has access to this data

    return response_handler(Data.saveNode(node_id, request.form))