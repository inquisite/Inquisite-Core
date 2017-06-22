import requests
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from flask_jwt_extended import JWTManager, jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity, get_raw_jwt, revoke_token
from werkzeug.security import safe_str_cmp
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth
from inquisite.db import db

from response_handler import response_handler

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/login', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type'])
def login():

    username = request.form.get('username')
    password = request.form.get('password')
    
    ret = {
      'status_code': 400,
      'payload': {
        'access_token': '',
        'msg': 'There was a problem authenticating'
      }
    }

    if username is not None and password is not None:
        db_user = db.run("MATCH (n:Person) WHERE n.email={username} RETURN n.name AS name, n.email AS email, n.password AS password, ID(n) AS user_id", {"username": username})

        ret['payload']['msg'] = "No user was found with that username, or your password was typed incorrectly" + username + "/" + password
        ret['status_code'] = 400

        for person in db_user:

            if sha256_crypt.verify(password, person['password']):
                ret['payload']['access_token'] = create_access_token(identity=username)
                ret['payload']['refresh_token'] = create_refresh_token(identity=username)
                ret['payload']['msg'] = "successful login"
                ret['payload']['user_id'] = person['user_id']
                ret['status_code'] = 200
                
    else:
        ret['payload']['msg'] = "Username and Password are required"
        ret['status_code'] = 422

    #print "ERROR CHECKING ..."
    #print ret

    return response_handler(ret)

# Refresh
@auth_blueprint.route('/refresh', methods=['POST'])
@crossdomain(origin='*', headers=['Authorization'])
@jwt_refresh_token_required
def refresh():
  current_user = get_jwt_identity()

  ret = {
    'status_code': 200,
    'payload': {
      'access_token': create_access_token(identity=current_user)
    }
  }

  return response_handler(ret)

# Logout
@auth_blueprint.route('/logout', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def logout():

    ret = {
      'status_code': '200',
      'payload': {
        'msg': 'Successfully logged out'
      }
    }

    try:
        current_token = get_raw_jwt()
        jti = current_token['jti']
        revoke_token(jti)
    except KeyError:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Access token not found in blacklist store'

    return response_handler(ret)

@auth_blueprint.route('/people/<person_id>/set_password', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setPassword(person_id):
    password = request.form.get('password')
    new_password = request.form.get('new_password')

    ret = {
      'status_code': '',
      'payload': {
        'msg': ''
      }
    }

    if password is not None and new_password is not None:

        # check if password and new pass are the same
        if password != new_password:

            db_password_hash = ''
            # check if password matches person_id
            result = db.run("MATCH (p:Person) WHERE ID(p)={person_id} RETURN p.password AS password", {"person_id": person_id})
            for p in result:
                db_password_hash = p['password']

            if db_password_hash != '':

                # hash new password and update DB
                new_pass_hash = sha256_crypt.hash(new_password)

                result = db.run("MATCH (p:Person) WHERE ID(p)={person_id} SET p.password = {new_pass_hash}", {"person_id": person_id, "new_pass_hash": new_pass_hash})

                # Check we updated something
                node_updated = False
                summary = result.consume()
                if summary.counters.properties_set >= 1:
                    node_updated = True

                if node_updated:
                    ret['status_code'] = 200
                    ret['payload']['msg'] = 'Password updated successfully'

            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'No user found'

        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'New Password is the same as current password'

    else:
        ret['status_code'] = 422
        ret['payload']['msg'] = 'Password and New Password needed to change password'

    return response_handler(ret)
