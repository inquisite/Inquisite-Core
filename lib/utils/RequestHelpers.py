import re
import json
from collections import OrderedDict
from flask import Response
from flask.json import jsonify

#
# Extract into a dictionary repeating parameters encoded thusly:
#
# name[0][key1] = some-value
# name[0][key2] = some-value
# name[0][key3] = some-value
# name[1][key1] = some-value
# name[1][key2] = some-value
# name[1][key3] = some-value
#
# Continuous numbering from zero of parameters is assumed.
#
def extractRepeatingParameterBlocksFromRequest(req, name):
    acc = {}
    for k in req.form:
        m = re.match("{0}\[([\d]+)\]\[([A-Za-z0-9\-_]+)\]".format(name), k)
        if m:
            i = int(m.group(1))
            sn = m.group(2)

            if i not in acc:
                acc[i] = {}
            acc[i][sn] = req.form.get(k)

    return acc

#
#
#
def extractRepeatingParameterFromRequest(req, name):
    acc = []
    for k in req.form:
        m = re.match("{0}\[([\d]+)\]".format(name), k)
        if m:
            acc.append(req.form.get(k))

    return acc

#
#
#
def responseHandler(return_object):

  mime_type = "application/json"
  if "mimetype" in return_object:
    mime_type = return_object['mimetype']

  status_code = return_object['status_code']

  resp = {}
  if "payload" in return_object:
    resp = return_object['payload']
  if "msg" in return_object:
    resp["msg"] = return_object["msg"]
  headers = {}
  if "headers" in return_object:
    headers = return_object["headers"]

  if "errors" in return_object:
    resp["errors"] = return_object["errors"]

  return Response(response=json.dumps(resp, encoding='latin1', ensure_ascii=False).encode('utf8', errors='ignore'), status=status_code, mimetype=mime_type, headers=headers)
#
# returnPayload = Return raw payload instead of request. [Default is false]
#
def makeResponse(status=200, message=None, payload=None, returnPayload=False, error=None, headers=None):
    if error:
        return makeErrorResponse(error, returnPayload=returnPayload)

    resp = {"status_code": status}
    if message is not None and len(message) > 0:
        resp['msg'] = message
    if payload is not None:
        resp['payload'] = payload
    if headers is not None:
        resp['headers'] = headers

    if returnPayload:
        return resp
    else:
        return responseHandler(resp)

#
#
#
def makeErrorResponse(e, status_code=400, returnPayload=False):
    if "context" in e:
        context = e.context
    else:
        context = ""

    resp = {
        "status_code": status_code,
        "msg": e.message,
        "context": context
    }
    if hasattr(e, "errors"):
        resp["errors"] = e.errors

    if returnPayload:
        return resp
    else:
        return responseHandler(resp)
