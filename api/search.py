from flask import Blueprint, request

from lib.managers.SearchManager import Search
from lib.utils.requestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.SearchError import SearchError

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/search', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def quick():
  try:
    return makeResponse(payload=Search.quick(request.args.get('q')))
  except SearchError as e:
    return makeResponse(error=e)
