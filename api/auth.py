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
from lib.crossDomain import crossdomain
from lib.basicAuth import check_auth, requires_auth
from lib.utils.Db import db

from lib.exceptions.AuthError import AuthError
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.SaveError import SaveError
from lib.exceptions.ValidationError import ValidationError
from lib.utils.RequestHelpers import makeResponse
from lib.managers.AuthManger import AuthManager
from lib.managers.PeopleManager import PeopleManager

auth_blueprint = Blueprint('auth', __name__)


#
# Perform login
#
@auth_blueprint.route('/login', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        return makeResponse(message="Login successful", payload=AuthManager.login(username, password))
    except AuthError as e:
        return makeResponse(error=e)

#
# Return new access token using refresh token
#
@auth_blueprint.route('/refresh', methods=['POST'])
@crossdomain(origin='*', headers=['Authorization'])
@jwt_refresh_token_required
def refresh():
  current_user = get_jwt_identity()

  try:
    return makeResponse(payload={'access_token': create_access_token(identity=current_user)})
  except Exception as e:
    return makeResponse(error=e)

#
# Perform logout
#
@auth_blueprint.route('/logout', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def logout():
    try:
        current_token = get_raw_jwt()
        jti = current_token['jti']
        revoke_token(jti)
        return makeResponse(payload={}, message="Logged out")
    except KeyError as e:
        return makeResponse(error=e)
    except Exception as e:
        return makeResponse(error=e)

#
# Reset user password
#
@auth_blueprint.route('/reset_password/<email_address>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def sendPasswordReset(email_address):
    try:
        if AuthManager.sendPasswordReset(email_address):
            msg = "Password reset"
        else:
            msg = "Password not changed"
        return makeResponse(message=msg, payload={})
    except AuthError as e:
        return makeResponse(error=e)

#
# Register new user
#
@auth_blueprint.route('/register', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def register():
    surname = request.form.get('surname')
    forename = request.form.get('forename')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')
    password = request.form.get('password')
    nyunetid = request.form.get('nyunetid')

    try:
        ret = PeopleManager.addPerson(forename, surname, location, email, nyunetid, url, tagline, password)
        return makeResponse(payload=ret, message="Added person")
    except DbError as e:
        return makeResponse(error=e)
    except SaveError as e:
        return makeResponse(error=e)
    except FindError as e:
        return makeResponse(error=e)
    except ValidationError as e:
        return makeResponse(error=e)
#
# Reset user password
#
@auth_blueprint.route('/people/<person_id>/set_password', methods=['GET', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def setPassword(person_id):
    #TODO: user may only set their own password by id; non-auth user can reset password with valid key

    password = request.form.get('password')

    try:
        if AuthManager.setPassword(person_id, password):
            msg = "Password changed"
        else:
            msg = "Password not changed"
        return makeResponse(message=msg, payload={})
    except FindError as e:
        return makeResponse(error=e)
    except AuthError as e:
        return makeResponse(error=e)