import os
import json
import collections
import datetime
from flask import Flask, request, current_app, make_response, session, escape, Response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_socketio import SocketIO
from neo4j.v1 import GraphDatabase, basic_auth
from lib.crossDomain import crossdomain


import simplekv.memory
import eventlet
#eventlet.monkey_patch()

# if sys.version_info < (3, 0):
#     sys.stdout.write("Sorry, requires Python 3.x, not Python 2.x\n")
#     sys.exit(1)

config = json.load(open('./config.json'));

# Init
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/uploads"

x_socketio = SocketIO()

def create_app():
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

    # Import blueprints
    from auth import auth_blueprint
    from banner import banner_blueprint
    from people import people_blueprint
    from organizations import organizations_blueprint
    from repos import repositories_blueprint
    from schema import schema_blueprint
    from data import data_blueprint
    from search import search_blueprint
    from upload import upload_blueprint
    from export import export_blueprint
    from list import list_blueprint
    from .sockets import sockets as socket_blueprint

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
    app.register_blueprint(socket_blueprint)
    app.register_blueprint(export_blueprint)
    app.register_blueprint(list_blueprint)

    x_socketio.init_app(app)
    return app, jwt
