import datetime
from functools import wraps, update_wrapper
from flask import request, make_response, current_app

# Cross Domain
# -- Based on http://flask.pocoo.org/snippets/56/
# could be replaced with https://flask-cors.readthedocs.io/en/latest/
def crossdomain(origin=None, methods=None, headers=None, max_age=21600, attatch_to_all=True, automatic_options=True):

  if methods is not None:
    methods = ', '.join(sorted(x.upper() for x in methods))
  if headers is not None and not isinstance(headers, str):
    headers = ', '.join(x.upper() for x in headers)
  if not isinstance(origin, str):
    origin = ', '.join(origin)
  if isinstance(max_age, datetime.timedelta):
    max_age = max_age.total_seconds()

  def get_methods():
    if methods is not None:
      return methods

    options_resp = current_app.make_default_options_response()
    return options_resp.headers['allow']

  def decorator(f):

    def wrapped_function(*args, **kwargs):

      if automatic_options and request.method == 'OPTIONS':
        resp = current_app.make_default_options_response()
      else:
        resp = make_response(f(*args, **kwargs))

      h = resp.headers
 
      h['Access-Control-Allow-Origin'] = origin
      h['Access-Control-Allow-Methods'] = get_methods()
      h['Access-Control-Max-Age'] = str(max_age)
      if headers is not None:
        h['Access-Control-Allow-Headers'] = headers

      resp.headers = h

      return resp

    f.provide_automatic_options = False
    f.required_methods = ['OPTIONS']
    return update_wrapper(wrapped_function, f)
  return decorator
