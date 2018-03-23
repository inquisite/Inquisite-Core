from flask import Blueprint, request

from lib.managers.ExportManager import ExportManager
from lib.utils.RequestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.SearchError import SearchError

export_blueprint = Blueprint('export', __name__)

@export_blueprint.route('/export', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def exportData():
  try:
    type = request.form.get('type')
    source = int(request.form.get('source'))
    print type, source
    return makeResponse(payload=ExportManager.export(type, source))
  except Exception as e:
    print e.message
    return makeResponse(error=e)
