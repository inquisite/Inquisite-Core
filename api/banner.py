from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from lib.utils.requestHelpers import makeResponse

banner_blueprint = Blueprint('banner', __name__)

#
# Output API banner
#
@banner_blueprint.route("/")
def index():
  return makeResponse(payload={
      'v1': "https://api.org/api/v1"
    })