import json
from inquisite.db import db
from neo4j.v1 import ResultError

class Organizations:

  # For Now All class methods are going to be static
  def __init__(self):
    pass


  @staticmethod
  def getAll():

    organizations = []
    result = db.run("Match (n:Organization) RETURN n.name AS name, pn.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")

    for o in result:
      organizations.append({
        "name": o['name'],
        "location": o['location'],
        "email": o['email'],
        "url": o['url'],
        "tagline": o['tagline']
      })

    return organizations

  @staticmethod
  def getInfo(organization_id):

    organization = {}
    result = db.run("MATCH (o:Organization) WHERE ID(o)={organization_id} RETURN o.name AS name, o.email AS email, " +
      "o.url AS url, o.location AS location, o.tagline AS tagline", {"organization_id": organization_id})

    for o in result:
      organization['name'] = o['name']
      organization['email'] = o['email']
      organization['url'] = o['url']
      organization['location'] = o['location']
      organization['tagline'] = o['tagline']
    
    return organization

  @staticmethod
  def delete(organization_id):

    del_success = False
    result = db.run("MATCH (o:Organization) WHERE ID(o)={organization_id} OPTIONAL MATCH (o)-[r]-() DELETE r,o", {"organization_id": organization_id})

    summary = result.consume()
    if summary.counters.nodes_deleted >= 1:
      del_success = True

    return del_success
  
  @staticmethod
  def getRepos(organization_id):
 
    repos = []
    result = db.run("MATCH (n:Repository)-[:PART_OF]->(o:Organization) WHERE ID(o)={organization_id} RETURN n.name AS name, n.url AS url, n.readme AS readme",
      {"organization_id": organization_id})

    for r in result:
      repos.append({
        "name": r['name'],
        "url": r['url'],
        "readme": r['readme']
      })

    return repos

  @staticmethod
  def addRepository(organization_id, repository_id):

    repository_added = False
    result = db.run("MATCH (o:Organization) WHERE ID(o)={organization_id} MATCH (r:Repository) WHERE ID(r)={repository_id} MERGE (r)-[:PART_OF]->(o)",
      {"organization_id": organization_id, "repository_id": repository_id})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      repository_added = True

    return repository_added

  @staticmethod
  def removeRepository(organization_id, repository_id):

    del_repository = False
    result = db.run("START r=node(*) MATCH (r)-[rel:PART_OF]->(o) WHERE ID(r)={repository_id} AND ID(o)={organization_id} DELETE rel",
      {"organization_id": organization_id, "repository_id": repository_id})

    summary = result.consume()
    if summary.counters.relationships_deleted >= 1:
      del_respository = True

    return del_repository

  @staticmethod
  def addPerson(organization_id, person_id):

    add_person = False
    result = db.run("MATCH (o:Organization) WHERE ID(o)={organization_id} MATCH (p:Person) WHERE ID(p)={person_id} " +
      "MERGE (p)-[:PART_OF]->(o)", {"organization_id": organization_id, "person_id": person_id})

    summary = result.consume()
    if summary.counters.relationship_created >= 1:
      add_person = True

    return add_person

  @staticmethod
  def removePerson(organization_id, person_id):

    del_person = False
    result = db.run("START p=node(*) MATCH (p)-[rel:PART_OF]->(n) WHERE ID(p)={person_id} AND ID(n)={organization_id} DELETE rel",
      {"organization_id": organization_id, "person_id": person_id})

    summary = result.consume()
    if summary.counters.relationships_deleted >= 1:
      del_person = True

    return del_person

  @staticmethod
  def getPeople(organization_id):

    people = []
    result = db.run("MATCH (n)-[:OWNED_BY|FOLLOWED_BY|MANAGED_BY|PART_OF]-(p) WHERE ID(n)={organization_id} RETURN p.name AS name, p.location AS location, " +
      "p.email AS email, p.url AS url, p.tagline AS tagline", {"organization_id": organization_id})

    for p in result:
      people.append({
        "name": p['name'],
        "location": p['location'],
        "email": p['email'],
        "url": p['url'],
        "tagline": p['tagline']
      })

    return people
