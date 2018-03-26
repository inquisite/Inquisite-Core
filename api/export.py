from flask import Blueprint, request, Response, make_response

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
    repo_id = int(request.form.get('repo'))
    schema_id = int(request.form.get('schema'))
    return makeResponse(payload=ExportManager.export(type, repo_id, schema_id), headers={"Content-disposition": "attachment; filename=tmp.json"})
  except Exception as e:
    print e.message
    return makeResponse(error=e)
