import os
import requests
import datetime
import time
import logging
import urllib
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

    # TODO validate params

    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': ''
        }
    }

    # TODO: check that repository is owned by current user

    try:
        result = db.run("MATCH (t:SchemaType{code: {code}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t", {"code": code, "repository_id": int(repository_id)}).peek()
        ret['payload']['msg'] = "Type already exists"
    except ResultError as e:
        result = db.run("MATCH (r:Repository) WHERE ID(r) = {repository_id} CREATE (t:SchemaType { name: {name}, code: {code}, description: {description}, storage: 'Graph' })-[:PART_OF]->(r) RETURN r",
                            {"repository_id": int(repository_id),"name": name, "code": code, "description": description})

        # TODO: clean up payload
        if result:
            ret['status_code'] = 200
            ret['payload']['msg'] = "Added type " + name + "//" + repository_id
            ret['payload']['type'] = "xxx"
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong saving new type'


    return response_handler(ret)

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

    # TODO validate params

    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': ''
        }
    }

    # TODO: check that repository is owned by current user

    try:
        result = db.run("MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t", {"typecode": typecode, "code": code, "repository_id": int(repository_id)}).peek()
        ret['payload']['msg'] = "Field already exists"
    except ResultError as e:
        result = db.run("MATCH (r:Repository)--(t:SchemaType {code: {typecode}}) WHERE ID(r) = {repository_id} CREATE (f:SchemaField { name: {name}, code: {code}, description: {description}, type: {fieldtype} })-[:PART_OF]->(t) RETURN r",
                            {"repository_id": int(repository_id),"name": name, "code": code, "description": description, "typecode": typecode, "fieldtype": fieldtype})
        print result.peek()
        # TODO: check query result

        # TODO: clean up payload
        if result:
            ret['status_code'] = 200
            ret['payload']['msg'] = "Added field " + name + "//" + repository_id
            ret['payload']['type'] = "xxx"
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong saving new field'


    return response_handler(ret)