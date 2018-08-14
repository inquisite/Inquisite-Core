from flask import Blueprint, request

from lib.managers.SearchManager import SearchManager
from lib.utils.RequestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.SearchError import SearchError

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/search', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def quick():
  try:
    return makeResponse(payload=SearchManager.quick(request.args.get('q')))
  except SearchError as e:
    return makeResponse(error=e)

@search_blueprint.route('/portalSearch', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def portal():
  try:
    return makeResponse(payload=SearchManager.portalSearch(request.args.get('q')))
  except SearchError as e:
    return makeResponse(error=e)

@search_blueprint.route('/portalBrowse', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def portalBrowse():
  try:
    return makeResponse(payload=SearchManager.portalBrowse(request.args.get('type')))
  except SearchError as e:
    return makeResponse(error=e)

@search_blueprint.route('/pagingSearch', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def paging():
  exp = request.args.get('q')
  node = request.args.get('n')
  try:
      start = int(request.args.get('s'))
      end = int(request.args.get('e'))
  except ValueError as e:
      return makeResponse(error=e)
  try:
    return makeResponse(payload=SearchManager.quick(exp, node, start, end))
  except SearchError as e:
    return makeResponse(error=e)
