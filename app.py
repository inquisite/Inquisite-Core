#!/bin/env python
from api import create_app, x_socketio

import os
import json
import collections
import datetime
from flask import Flask, request, current_app, make_response, session, escape, Response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from neo4j.v1 import GraphDatabase, basic_auth
from lib.crossDomain import crossdomain

import sys

app, jwt = create_app()

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
    x_socketio.run(app)
