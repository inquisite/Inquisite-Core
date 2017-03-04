from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from response_handler import response_handler

banner_blueprint = Blueprint('banner', __name__)

@banner_blueprint.route("/")
def index():
  ret = {
    'status_code': 200,
    'payload': {
      'v1': "https://inquisite.org/api/v1"
    }
  }

  return response_handler(ret)

