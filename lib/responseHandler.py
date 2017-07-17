# Response Handler Helper

import json
from collections import OrderedDict
from flask import Response

def response_handler(return_object):

  mime_type = "application/json"
  if "mimetype" in return_object:
    mime_type = return_object['mimetype']

  status_code = return_object['status_code']
  resp = return_object['payload']  

  return Response(response=json.dumps(resp).encode('utf8'), status=status_code, mimetype=mime_type)
