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
from flask import Flask, Blueprint, request, current_app, make_response, session, escape, Response
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import safe_str_cmp
from neo4j.v1 import GraphDatabase, basic_auth
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth


auth_blueprint = Blueprint('auth', __name__)


config = json.load(open('./config.json'));
driver = GraphDatabase.driver(config['database_url'], auth=basic_auth(config['database_user'],config['database_pass']))
db_session = driver.session()

@auth_blueprint.route('/login', methods=['POST'])
@crossdomain(origin='*')
def login():

    username = request.form.get('username')
    password = request.form.get('password')

    # logging.warning("username: " + username)
    # logging.warning("password: " + password)

    if username is not None and password is not None:
        db_user = db_session.run(
            "MATCH (n:Person) WHERE n.email='" + username + "' RETURN n.name AS name, n.email AS email, n.password AS password, ID(n) AS user_id")

        for person in db_user:
            # if pwd_context.verify(password, person['password']):
            if sha256_crypt.verify(password, person['password']):
                logging.warning('password verified. login success!')
                ret = {'access_token': create_access_token(identity=username), 'email': person['email'],
                       'user_id': person['user_id']}
                return Response(response=json.dumps(ret), status=200, mimetype="application/json")

        # We didn't find anyone
        ret = {"status": "err",
               "msg": "No user was found with that username, or your password was typed incorrectly"}
        return Response(response=json.dumps(ret), status=422, mimetype="application/json")

    else:

        resp = (("status", "err"),
                ("msg", "username and password are required"))
        resp = collections.OrderedDict(resp)
        return Response(response=json.dumps(resp), status=200, mimetype="application/json")

# Logout
@auth_blueprint.route('/logout')
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def logout():
    db_session.pop('username', None)


@auth_blueprint.route('/people/<person_id>/set_password', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setPassword(person_id):
    password = request.form.get('password')
    new_password = request.form.get('new_password')

    if password is not None and new_password is not None:

        # check if password and new pass are the same
        if password != new_password:

            db_password_hash = ''
            # check if password matches person_id
            result = db_session.run("MATCH (p:Person) WHERE ID(p)=" + person_id + " RETURN p.password AS password")
            for p in result:
                db_password_hash = p['password']

            if db_password_hash != '':

                # hash new password and update DB
                new_pass_hash = sha256_crypt.hash(new_password)

                result = db_session.run(
                    "MATCH (p:Person) WHERE ID(p)=" + person_id + " SET p.password = '" + new_pass_hash + "'")

                # Check we updated something
                node_updated = False
                summary = result.consume()
                if summary.counters.properties_set >= 1:
                    node_updated = True

                if node_updated:
                    resp = (("status", "ok"),
                            ("msg", "Password updated successfully"))

            else:
                resp = (("status", "err"),
                        ("msg", "No user found for that person_id"))

        else:
            resp = (("status", "err"),
                    ("msg", "New password is the same as current password"))

    else:
        resp = (("status", "err"),
                ("msg", "password and new password needed to change password"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")