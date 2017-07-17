from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from lib.models.dataClass import Data
from response_handler import response_handler
from simpleCrossDomain import crossdomain

data_blueprint = Blueprint('data', __name__)

@data_blueprint.route('/data/getNode/<node_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getNode(node_id):
    return response_handler(Data.getNode(node_id))

@data_blueprint.route('/data/saveNode/<node_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def saveNode(node_id):
    return response_handler(Data.saveNode(node_id, request.form))