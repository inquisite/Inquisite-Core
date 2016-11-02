import json
import requests
import collections
import datetime
import time
import logging
from passlib.apps import custom_app_context as pwd_context
from usermodel import User
from functools import wraps, update_wrapper
from flask import Flask, request, current_app, make_response, session, escape, Response
from neo4j.v1 import GraphDatabase, basic_auth
app = Flask(__name__)


# Cross Domain
# -- Based on http://flask.pocoo.org/snippets/56/
# could be replaced with https://flask-cors.readthedocs.io/en/latest/
def crossdomain(origin=None, methods=None, headers=None, max_age=21600, attatch_to_all=True, automatic_options=True):

  if methods is not None:
    methods = ', '.join(sorted(x.upper() for x in methods))
  if headers is not None and not isinstance(headers, basestring):
    headers = ', '.join(x.upper() for x in headers)
  if not isinstance(origin, basestring):
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

# HTTP Basic Auth
def check_auth(username, password):
  """This function is called to check if a username / password combination is valid."""
  
  retval = False
  if username:
    db_hash = ""
    db_user = session.run("MATCH (n:Person) WHERE n.email='" + username + "' RETURN n.name AS name, n.password AS password")
    if db_user:
      for user in db_user:
        db_hash = user['password']

    retval = pwd_context.verify(password, db_hash)

  return retval

def authenticate():
  """Sends a 401 response that enables basic auth"""

  return Response('Could not verify your access level for that URL.\n'
                  'You have to login with proper credentials', 401,
                  {'WWW-Authenticate': 'Basic realm="Login Requrired"'})


def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
      return authenticate()
    return f(*args, **kwargs)
  return decorated


driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j","drumroll"))
session = driver.session()

@app.route("/")
def index():

  resp = (("status", "ok"),
          ("v1", "http://inquisite.whirl-i-gig.com/api/v1"))
  resp = collections.OrderedDict(resp)

  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

# Login
@app.route('/login', methods=['POST'])
def login():

  print "in login"

  email  = request.args.get('username')
  passwd = request.args.get('password')

  if email is not None and passwd is not None:

    db_user = session.run("MATCH (n:Person) WHERE n.email='" + email + "' RETURN n.name AS name, n.password AS password")
    if db_user:
      for user in db_user:

        if pwd_context.verify(passwd, user['password']):

          session['username'] = email
          resp = (("status", "ok"),
                  ("msg", email + " logged in successfully"))
          
    else:
      resp = (("status", "err"),
              ("msg", "That username was not found"))

  else:
    resp = (("status", "err"),
            ("msg", "Username and password are required"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="applications/json")  

# Logout
@app.route('/logout')
@requires_auth
def logout():
  session.pop('username', None)


# People
@app.route('/people', methods=['GET'])
@requires_auth
def peopleList():

  persons = []
  people = session.run("MATCH (n:Person) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")
  for p in people:
    persons.append({
      "name": p['name'],
      "location": p['location'],
      "email": p['email'],
      "url": p['url'],
      "tagline": p['tagline']
    })

  resp = (("status", "ok"),
          ("people", persons))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/add', methods=['POST'])
@crossdomain(origin='*')
def addPerson():

  logging.warning("in addPerson")

  name     = request.form.get('name')
  location = request.form.get('location')
  email    = request.form.get('email')
  url      = request.form.get('url')
  tagline  = request.form.get('tagline')
  password = request.form.get('password')

  logging.warning( "name: " + name )
  logging.warning( "location: " + location )
  logging.warning( "email: " + email )
  logging.warning( "url: " + url )
  logging.warning( "tagline: " + tagline )
  logging.warning( "password: " + password )

  if password is not None:
    user = User()
    User.hash_password(user, password)

    password_hash = user.password_hash
    ts            = time.time()
    created_on    = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    result = session.run("CREATE (n:Person {url: '" + url + "', name: '" + name + "', email: '" + email 
      + "', location: '" + location + "', tagline: '" + tagline + "', password: '" + password_hash + "', created_on: '" + created_on + "'})") 

    if result:
      resp = (("status", "ok"),
            ("msg", name + " added"))
    else:
      resp = (("status", "err"),
            ("msg", "Something went wrong saving Person"))

  else:
    resp = (("status", "err"),
            ("msg", "User Password is required"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/edit', methods=['POST'])
@requires_auth
def editPerson(person_id):
 
  name     = request.args.get('name')
  location = request.args.get('location')
  email    = request.args.get('email')
  url      = request.args.get('url')
  tagline  = request.args.get('tagline')

  update = []
  if name is not None:
    update.append("p.name = '" + name + "'")

  if location is not None:
    update.append("p.location = '" + location + "'")

  if email is not None:
    update.append("p.email = '" + email + "'")

  if url is not None:
    update.append("p.url = '" + url + "'")

  if tagline is not None:
    update.append("p.tagline = '" + tagline + "'")


  update_str = "%s" % ", ".join(map(str, update))

  updated_person = {}
  yyresult = session.run("MATCH (p:Person) WHERE ID(p)=" + person_id + " SET " + update_str + 
    " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline")

  for p in result:
    updated_person['name'] = p['name']
    updated_person['location'] = p['location']
    updated_person['email'] = p['email']
    updated_person['url'] = p['url']
    updated_person['tagline'] = p['tagline']

  if result:
    resp = (("status", "ok"),
            ("msg", "Person updated"),
            ("person", updated_person))
  else:
    resp = (("status", "err"),
            ("msg", "problem updating Person"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/delete', methods=['POST'])
@requires_auth
def deletePerson(person_id):
  
  result = session.run("MATCH (n:Person) WHERE ID(n)=" + person_id + " OPTIONAL MATCH (n)-[r]-() DELETE r,n")

  if result:
    resp = (("status", "ok"),
            ("msg", "Peson Deleted Successfully"))
  else:
    resp = (("status", "err"),
            ("msg", "Something went wrong deleting Person"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/repos', methods=['GET'])
@requires_auth
def getPersonRepos(person_id):

  result = session.run("MATCH (n)<-[:OWNS|FOLLOWS|COLLABORATES_WITH]-(p) WHERE ID(p)=" + person_id + " RETURN n")

  print "Looking for repos ..."
  print result

  repos = []
  for item in result:
    print "going through items ... "
    print item 

  if result:
    resp = (("status", "ok"),
            ("repos", repos))
  else:
    resp = (("status", "err"),
            ("msg", "error getting repos for Person"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/set_password', methods=['POST'])
@requires_auth
def setPassword(person_id):

  password  = request.args.get('password')

  # TODO: Look into neo4j user authentication / encryption

# Organizations
@app.route('/organizations', methods=['GET'])
@requires_auth
def orgList():
  
  orgslist = []
  orgs = session.run("MATCH (n:Organization) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")
  for o in orgs:
    orgslist.append({
      "name": o['name'],
      "location": o['location'],
      "email": o['email'],
      "url": o['url'],
      "tagline": o['tagline']
    })  

  resp = (("status", "ok"),
          ("orgs", orgslist))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/add', methods=['POST'])
@requires_auth
def addOrg():

  name     = request.args.get('name')
  location = request.args.get('location')
  email    = request.args.get('email')
  url      = request.args.get('url')
  tagline  = request.args.get('tagline')
  
  result = session.run("CREATE (o:Organization {name: '" + name + "', location: '" + location + "', email: '" + email + "', url: '" + url + 
    "', tagline: '" + tagline + "'})")

  if result:
    resp = (("status", "ok"),
            ("msg", "Organization Added"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding Organization"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/edit', methods=['POST'])
@requires_auth
def editOrg(org_id):

  name     = request.args.get('name')
  location = request.args.get('location')
  email    = request.args.get('email')
  url      = request.args.get('url')
  tagline  = request.args.get('tagline')

  update = []
  if name is not None:
    update.append("o.name = '" + name + "'")

  if location is not None:
    update.append("o.location = '" + location + "'")

  if email is not None:
    update.append("o.email = '" + email + "'")

  if url is not None:
    update.append("o.url = '" + url + "'")

  if tagline is not None:
    update.append("o.tagline = '" + tagline + "'")

  update_str = "%s" % ", ".join(map(str, update))

  updated_org = {}
  result = session.run("MATCH (o:Organization) WHERE ID(o)=" + org_id + " SET " + update_str + 
    " RETURN o.name AS name, o.location AS location, o.email AS email, o.url AS url, o.tagline AS tagline")

  for o in result:
    updated_org['name'] = o['name']
    updated_org['location'] = o['location']
    updated_org['email'] = o['email']
    updated_org['url'] = o['url']
    updated_org['tagline'] = o['tagline']

  if result:
    resp = (("status", "ok"),
            ("msg", "Organization updated"),
            ("org", updated_org))
  else:
    resp = (("status", "err"),
            ("msg", "Problem updating Organization"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/delete', methods=['GET'])
@requires_auth
def deleteOrg(org_id):

  result = session.run("MATCH (o:Organization) WHERE ID(o)=" + org_id + " OPTIONAL MATCH (o)-[r]-() DELETE r,o")
  if result:
    resp = (("status", "ok"),
            ("msg", "Organization deleted"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem deleting Organizatin"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/repos', methods=['GET'])
@requires_auth
def getOrgRepos(org_id):

  result = session.run("MATCH (n)<-[:PART_OF]-(o) WHERE ID(o)=" + org_id + " RETURN n")
  if result:
    resp = (("status", "ok"),
            ("repos", result))
  else:
    resp = (("status", "err"),
            ("msg", "problem getting repos for Organization"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/add_person/<person_id>', methods=['POST'])
@requires_auth
def addPersonToOrg(org_id, person_id):

  result = session.run("MATCH (o:Organization) WHERE ID(o)=" + org_id + " MATCH (p:Person) WHERE ID(p)=" + person_id +
    " MERGE (p)-[:PART_OF]->(o)")

  if result: 
    resp = (("status", "ok"),
            ("msg", "Person is part of Org"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding person to org"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/remove_person/<person_id>', methods=['POST'])
@requires_auth
def removePersonFromOrg(org_id, person_id):

  result = session.run("START p=node(*) MATCH (p)-[rel:PART_OF]->(n) WHERE ID(p)=" + person_id + " AND ID(n)=" + org_id + " DELETE rel")
  if result:
    resp = (("status", "ok"),
            ("msg", "removed person from org"))
  else:
    resp = (("status", "err"),
            ("msg", "problem removing person from org"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/people', methods=['GET'])
@requires_auth
def getOrgPeople(org_id):

  org_people = []
  result = session.run("MATCH (n)-[:OWNED_BY|FOLLOWED_BY|MANAGED_BY|PART_OF]-(p) WHERE ID(n)=" + org_id + 
    " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline")
  for p in result:
    org_people.append({
      "name": p['name'],
      "location": p['location'],
      "email": p['email'],
      "url": p['url'],
      "tagline": p['tagline']
    })  

  resp = (("status", "ok"),
          ("people", org_people))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

# Repositories
@app.route('/repositories', methods=['GET'])
@requires_auth
def repoList():

  repos = []
  result = session.run("MATCH (n:Repository) RETURN n.url AS url, n.name AS name, n.readme AS readme")
  for r in result:
    repos.append({
      "name": r['name'],
      "url": r['url'],
      "readme": r['readme']
    })

  resp = (("status", "ok"),
          ("repos", repos))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/add', methods=['POST'])
@requires_auth
def addRepo():

  url    = request.args.get('url')
  name   = request.args.get('name')
  readme = request.args.get('readme')
  
  ts = time.time()
  created_on    = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

  result = session.run("CREATE (n:Repository {url: '" + url + "', name: '" + name + "', readme: '" + readme + 
    "', created_on: '" + created_on + "'})")
  if result:
    resp = (("status", "ok"),
            ("msg", "Created Repo"))
  else:
    resp = (("status", "err"),
            ("msg", "problem creating repo"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/edit', methods=['POST'])
@requires_auth
def editRepo(repo_id):

  url    = request.args.get('url')
  name   = request.args.get('name')
  readme = request.args.get('readme')

  update = []
  if name is not None:
    update.append("n.name = '" + name + "'")

  if url is not None:
    update.append("n.url = '" + url + "'")

  if readme is not None:
    update.append("n.readme = '" + readme + "'")

  update_str = "%s" % ", ".join(map(str, update))

  updated_repo = {}
  result = session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " SET " + update_str + 
    " RETURN n.name AS name, n.url AS url, n.readme AS readme")

  for r in result:
    updated_repo['name'] = r['name']
    updated_repo['url'] = r['url']
    updated_repo['readme'] = r['readme']

  if result:
    resp = (("status", "ok"),
            ("msg", "Repository updated"),
            ("repo", updated_repo))
  else:
    resp = (("status", "err"),
            ("msg", "Problem updating Repo"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/delete', methods=['GET'])
@requires_auth
def deleteRepo(repo_id):

  result = session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " OPTIONAL MATCH (o)-[r]-() DELETE r,o")
  if result:
    resp = (("status", "ok"),
            ("msg", "Repo deleted"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem deleting repo"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/owner', methods=['GET'])
@requires_auth
def getRepoOwner(repo_id):

  owner = {}
  result = session.run("MATCH (n)<-[:OWNED_BY]-(p) WHERE ID(n)=" + repo_id + 
    " RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline")
  for r in result:
    owner['name']     = r['name']
    owner['location'] = r['location']
    owner['email']    = r['email']
    owner['url']      = r['url']
    owner['tagline']  = r['tagline']

  if result:
    resp = (("status", "ok"),
            ("owner", owner))
  else:
    resp = (("status", "err"),
            ("msg", "could not retreive owner"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>', methods=['GET'])
@requires_auth
def getRepoInfo(repo_id):

  repo = {}
  result = session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " RETURN n.name AS name, n.url AS url, n.readme AS readme")
  for r in result:
    repo['name']   = r['name']
    repo['url']    = r['url']
    repo['readme'] = r['readme']

  if result:
    resp = (("status", "ok"),
            ("repo", repo ))
  else:
    resp = (("status", "err"),
            ("msg", "could not return repo info"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/add_collaborator/<person_id>', methods=['POST'])
@requires_auth
def addRepoCollab(repo_id, person_id):

  result = session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " MATCH (p:Person) WHERE ID(p)=" + person_id +
    " MERGE (p)-[:COLLABORATES_WITH]->(n)")

  if result:
    resp = (("status", "ok"),
            ("msg", "Collaborator Added"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding Collaborator"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/remove_collaborator/<person_id>', methods=['POST'])
@requires_auth
def removeRepoCollab(repo_id, person_id):

  result = session.run("START p=node(*) MATCH (p)-[rel:COLLABORATES_WITH]->(n) WHERE ID(p)=" + person_id + " AND ID(n)=" + repo_id + " DELETE rel")
  if result:
    resp = (("status", "ok"),
            ("msg", "Collaborator removed"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem removing collaborator"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")
 
@app.route('/repositories/<repo_id>/add_follower/<person_id>', methods=['POST'])
@requires_auth
def addRepoFollower(repo_id, person_id):

  result = session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " MATCH (p:Person) WHERE ID(p)=" + person_id +
    " MERGE (p)-[:FOLLOWS]->(n)")
  if result:
    resp = (("status", "ok"),
            ("msg", "Folower Added"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding follower"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/remove_follower/<person_id>', methods=['POST'])
@requires_auth
def removeRepoFollower(repo_id, person_id):

  result = session.run("START p=node(*) MATCH (p)-[rel:FOLLOWS]->(n) WHERE ID(p)=" + person_id + " AND ID(n)=" + repo_id + " DELETE rel")
  if result:
    resp = (("status", "ok"),
            ("msg", "Follower Removed"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem removing follower"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/add_data_node', methods=['POST'])
@requires_auth
def addRepoData(repo_id):

  result = session.run()


@app.route('/repositories/<repo_id>/query', methods=['POST'])
@requires_auth
def queryRepo(repo_id):

  result = session.run()

@app.route('/repositories/<repo_id>/get_all_data', methods=['GET'])
@requires_auth
def getRepoData(repo_id):

  result = session.run()

@app.route('/repositories/<repo_id>/set_entry_point', methods=['POST'])
@requires_auth
def setEntryPoint(repo_id):

  result = session.run()

@app.errorhandler(404)
def page_not_found(e):

  resp = (("status", "err"),
          ("msg", "The request could not be completed"))

  resp = collectons.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=404, mimetype="application/json")

if __name__ == '__main__':
  app.run()
