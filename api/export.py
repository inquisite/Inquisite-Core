from flask import Blueprint, request, Response, make_response
import json

from lib.managers.ExportManager import ExportManager
from lib.utils.RequestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.SearchError import SearchError

export_blueprint = Blueprint('export', __name__)

@export_blueprint.route('/export', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def exportData():
  type = request.form.get('type')
  try:
    repo_id = int(request.form.get('repo'))
  except TypeError:
    repo_id = None
  try:
    schema_id = int(request.form.get('schema'))
  except TypeError:
    schema_id = None
  try:
    record_ids = json.loads(request.form.get('records'))
  except TypeError:
    record_ids = None
  try:
    return makeResponse(payload=ExportManager.export(type, repo_id, schema_id, record_ids), headers={"Content-disposition": "attachment; filename=tmp.json"})
  except Exception as e:
    print "endpoint", e.message
    return makeResponse(error=e)
