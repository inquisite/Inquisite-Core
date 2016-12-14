from functools import wraps

# HTTP Basic Auth
def check_auth(username, password):
  """This function is called to check if a username / password combination is valid."""
  
  retval = False
  if username:
    db_hash = ""
    db_user = db_session.run("MATCH (n:Person) WHERE n.email='" + username + "' RETURN n.name AS name, n.password AS password")
    if db_user:
      for user in db_user:
        db_hash = user['password']

    retval = pwd_context.verify(password, db_hash)

  return retval


def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
      return authenticate()
    return f(*args, **kwargs)
  return decorated
