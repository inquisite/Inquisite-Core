import json
from inquisite.db import db
from neo4j.v1 import ResultError
from repositoriesClass import Repositories

class People:
  identity = None
  identity_type = None

  # For Now All class methods are going to be static

  def __init__(self, id, id_type):
    identity = id
    identity_type = id_type


  @staticmethod
  def getAll():

    persons = []
    result = db.run("Match (p:Person) RETURN ID(n) AS id, p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline")

    for p in result:
      persons.append({
        "id": p['id'],
        "name": p['name'],
        "location": p['location'],
        "email": p['email'],
        "url": p['url'],
        "tagline": p['tagline']
      })

    return persons

  @staticmethod
  def getInfo(identity, ident_str):

    person = {}
    result = db.run("MATCH (p:Person) WHERE " + ident_str + " RETURN ID(p) AS id, p.name AS name, p.email AS email, " +
      "p.url AS url, p.location AS location, p.tagline AS tagline, p.prefs AS prefs", {"identity": identity})

    for p in result:
      prefs = {}
      if (p['prefs'] != None):
        prefs = json.loads(p['prefs'])
      person['id'] = p['id']
      person['name'] = p['name']
      person['email'] = p['email']
      person['url'] = p['url']
      person['location'] = p['location']
      person['tagline'] = p['tagline']
      person['prefs'] = prefs 
    
    return person

  @staticmethod
  def getRepos(identity, ident_str):

    print "in getRepos .. checking ident and string"
    print "identity" + str(identity)
    print "ident_str" + ident_str

    repos = []
    result = db.run("MATCH (n)<-[:OWNED_BY|COLLABORATES_WITH]-(p) WHERE " + ident_str + " RETURN ID(n) AS id, n.name AS name, n.readme As readme, " +
      "n.url AS url, n.created_on AS created_on", {"identity": identity})

    for item in result:

      data  = Repositories.getData( int(item['id']) )
      users = Repositories.getUsers( int(item['id']) )

      repos.append({
        "id": item['id'],
        "name": item['name'],
        "readme": item['readme'],
        "created_on": item['created_on'],
        "url": item['url'],
        "data": data,
        "users": users
      })

    print "Returning repos for person"
    print repos
    return repos
