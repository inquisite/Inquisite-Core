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
from inquisite.db import db
from neo4j.v1 import ResultError
from lib.schema import addType, addField, addDataToRepo

from response_handler import response_handler
from xlsdata import XlsHandler

schema_blueprint = Blueprint('schema', __name__)

@schema_blueprint.route('/schema/addType/<repository_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addType(repository_id):
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')

    return response_handler(addType(repository_id, name, code, description))

@schema_blueprint.route('/schema/editType/<repository_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editType():
    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': 'arg'
        }
    }

    return response_handler(ret)

@schema_blueprint.route('/schema/removeType/<repository_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeType():


    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': 'arg'
        }
    }

    return response_handler(ret)

@schema_blueprint.route('/schema/addField/<repository_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addField(repository_id, typecode):
    name = request.form.get('name')
    code = request.form.get('code')
    fieldtype = request.form.get('type')
    description = request.form.get('description')

    return response_handler(addField(repository_id, typecode, name, code, fieldtype, description))

@schema_blueprint.route('/schema/addData/<repository_id>/<typecode>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addData(repository_id, typecode):
    data = request.form.get('data')

    return response_handler(addDataToRepo(repository_id, typecode, json.loads(data)))
