from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from response_handler import response_handler

banner_blueprint = Blueprint('banner', __name__)

#
# Output API banner
#
@banner_blueprint.route("/")
def index():
  ret = {
    'status_code': 200,
    'payload': {
      'v1': "https://api.org/api/v1"
    }
  }

  return response_handler(ret)

