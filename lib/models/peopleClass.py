import json

from lib.models.repositoriesClass import Repositories
from lib.utils.db import db


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
    result = db.run("Match (p:Person) RETURN ID(p) AS id, p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline")

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
        try:
          prefs = json.loads(p['prefs'])
        except:
          prefs = {}

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

    repos = []
    result = db.run("MATCH (n:Repository)<-[:OWNED_BY|COLLABORATES_WITH]-(p) WHERE " + ident_str + " RETURN ID(n) AS id, n.name AS name, n.readme As readme, " +
      "n.url AS url, n.created_on AS created_on", {"identity": identity})

    for item in result:

      owner = Repositories.getOwner( int(item['id']) )
      data  = Repositories.getData( int(item['id']) )
      users = Repositories.getUsers( int(item['id']) )

      repos.append({
        "id": item['id'],
        "name": item['name'],
        "readme": item['readme'],
        "created_on": item['created_on'],
        "url": item['url'],
        "data": data,
        "users": users,
        "owner": owner,
        "schema_type_count" : 0,
        "schema_field_count" : 0,
        "data_element_count": 0
      })

    for item in repos:
      result = db.run(
        "MATCH (n:Repository)--(t:SchemaType)--(d:Data) WHERE ID(n) = {repository_id} RETURN count(d) as data_element_count", {"repository_id": int(item['id'])})
      for r in result:
          item['data_element_count'] = r['data_element_count']

      result = db.run(
        "MATCH (n:Repository)--(t:SchemaType)--(f:SchemaField) WHERE ID(n) = {repository_id} RETURN count(DISTINCT(t)) as schema_type_count, count(DISTINCT(f)) as schema_field_count",
        {"repository_id": int(item['id'])})
      for r in result:
        item['schema_type_count'] = r['schema_type_count']
        item['schema_field_count'] = r['schema_field_count']
    return repos


  @staticmethod
  def find(params):
    people = []

    criteria = []

    if ('name' in params) and (params['name']) and len(params['name']) > 0:
      params['name'] = params['name'].lower()
      criteria.append("lower(p.name) CONTAINS {name}")
    if ('email' in params) and (params['email']) and len(params['email']) > 0:
      params['email'] = params['email'].lower()
      criteria.append("lower(p.email) STARTS WITH {email}")

    if len(criteria) == 0:
      return None


    result = db.run("MATCH (p:Person) WHERE " + " OR ".join(criteria) + " RETURN ID(p) AS id, p.name AS name, p.email AS email, " +
                    "p.url AS url, p.location AS location, p.tagline AS tagline",
                    params)

    for p in result:
      r = {}
      for f in ['id', 'name', 'email', 'url', 'location', 'tagline']:
        r[f] = p[f]
      people.append(r)

    return people