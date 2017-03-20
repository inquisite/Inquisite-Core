import os
import json
import requests
import collections
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, request, current_app, make_response, session, escape, Response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import safe_str_cmp
from neo4j.v1 import GraphDatabase, basic_auth
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth

from response_handler import response_handler

from inquisite.auth import auth_blueprint
from inquisite.banner import banner_blueprint
from inquisite.people import people_blueprint
from inquisite.organizations import organizations_blueprint
from inquisite.repositories import repositories_blueprint
from inquisite.schema import schema_blueprint
import simplekv.memory

config = json.load(open('./config.json'));

# Init
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/uploads"


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = config['auth_secret']
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_STORE'] = simplekv.memory.DictStore()
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = 'all'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=15)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

driver = GraphDatabase.driver(config['database_url'], auth=basic_auth(config['database_user'],config['database_pass']))
db_session = driver.session()

# start jwt service
jwt = JWTManager(app)

# register API modules
app.register_blueprint(banner_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(people_blueprint)
app.register_blueprint(organizations_blueprint)
app.register_blueprint(repositories_blueprint)
app.register_blueprint(schema_blueprint)



@jwt.expired_token_loader
@crossdomain(origin='*', attatch_to_all=True, headers=['Content-Type', 'Authorization'])
def my_expired_token_callback():
    return jsonify({
        'status': 401,
        'msg': 'The token has expired'
    }), 200

@app.errorhandler(404)
def page_not_found(e):

  resp = (("status", "err"),
          ("msg", "The request could not be completed"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=404, mimetype="application/json")

if __name__ == '__main__':
  app.run()
