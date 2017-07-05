import json
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_raw_jwt, revoke_token
from werkzeug.security import safe_str_cmp
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth
from inquisite.db import db
from lib.peopleClass import People

from response_handler import response_handler
from lib.searchClass import Search

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/search', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def quick():
  return response_handler(Search.quick(request.args.get('q')))

