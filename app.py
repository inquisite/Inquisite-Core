import os
import json
import collections
import datetime
from flask import Flask, request, current_app, make_response, session, escape, Response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from neo4j.v1 import GraphDatabase, basic_auth
from lib.crossDomain import crossdomain

from api.auth import auth_blueprint
from api.banner import banner_blueprint
from api.people import people_blueprint
from api.organizations import organizations_blueprint
from api.repos import repositories_blueprint
from api.schema import schema_blueprint
from api.data import data_blueprint
from api.search import search_blueprint
from api.upload import upload_blueprint
import simplekv.memory

import sys
# if sys.version_info < (3, 0):
#     sys.stdout.write("Sorry, requires Python 3.x, not Python 2.x\n")
#     sys.exit(1)

config = json.load(open('./config.json'));

# Init
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/uploads"


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = config['auth_secret']
app.config['JWT_BLACKLIST_ENABLED'] = False
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
app.register_blueprint(search_blueprint)
app.register_blueprint(data_blueprint)
app.register_blueprint(upload_blueprint)


@jwt.expired_token_loader
@crossdomain(origin='*', attatch_to_all=True, headers=['Content-Type', 'Authorization'])
def expired_token_callback():
    resp = {
        'status': 401,
        'msg': 'The token has expired'
    }
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.errorhandler(401)
@crossdomain(origin='*', attatch_to_all=True, headers=['Content-Type', 'Authorization'])
def auth_failed(e):

  resp = (("status", "err"),
          ("msg", "The request could not be completed"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=401, mimetype="application/json")

@app.errorhandler(404)
@crossdomain(origin='*', attatch_to_all=True, headers=['Content-Type', 'Authorization'])
def page_not_found(e):

  resp = (("status", "err"),
          ("msg", "The request could not be completed"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=404, mimetype="application/json")

if __name__ == '__main__':
  app.run()
