from flask import Blueprint, request

from lib.models.searchClass import Search
from lib.responseHandler import response_handler
from lib.crossDomain import crossdomain

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/search', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def quick():
  return response_handler(Search.quick(request.args.get('q')))

