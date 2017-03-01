import collections
import json
from flask import Flask, Blueprint, request, current_app, make_response, session, escape, Response

banner_blueprint = Blueprint('banner', __name__)

@banner_blueprint.route("/")
def index():
  resp = (("status", "ok"),
          ("v1", "https://inquisite.org/api/v1"))
  resp = collections.OrderedDict(resp)

  return Response(response=json.dumps(resp), status=200, mimetype="application/json")