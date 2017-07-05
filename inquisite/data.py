import os
import requests
import datetime
import time
import logging
import urllib
import json
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_raw_jwt
from werkzeug.security import safe_str_cmp
from werkzeug.utils import secure_filename
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth
from lib.utils import makeDataMapForCypher

from inquisite.db import db

from lib.dataClass import Data
from response_handler import response_handler
from xlsdata import XlsHandler


data_blueprint = Blueprint('data', __name__)

@data_blueprint.route('/data/getNode/<node_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
#@jwt_required
def getNode(node_id):
    return response_handler(Data.getNode(node_id))

@data_blueprint.route('/data/saveNode/<node_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
#@jwt_required
def saveNode(node_id):
    return response_handler(Data.saveNode(node_id, request.form))