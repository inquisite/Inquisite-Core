import json
import time
import datetime
from inquisite.db import db

class Repositories:

  # For Now All class methods are going to be static
  def __init__():
    pass 

  @staticmethod
  def getAll():

    repos = []
    result = db.run("MATCH (n:Repository) RETURN n.url AS url, n.name AS name, n.readme AS readme")
   
    for r in result:
      repos.append({
        "name": r['name'],
        "url": r['url'],
        "readme": r['readme']
      })

    return repos

  @staticmethod
  def nameCheck(name):
    res = db.run("MATCH (n:Repository {name: {name}}) RETURN n", {"name": name})
    if len(list(res)) > 0:
      return False
    else:
      return True    

  @staticmethod
  def create(url, name, readme, identity, ident_str):
       
      ts = time.time()
      created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

      new_repo = {}
      result = db.run("CREATE (n:Repository {url: {url}, name: {name}, readme: {readme}, created_on: {created_on}}) " +
        "RETURN n.url AS url, n.name AS name, n.readme AS readme, ID(n) AS repo_id", {"url": url, "name": name, "readme": readme, "created_on": created_on})

      for r in result:
        new_repo['id'] = r['repo_id']
        new_repo['url'] = r['url']
        new_repo['name'] = r['name']
        new_repo['readme'] = r['readme']

      repo_created = False
      summary = result.consume()
      if summary.counters.nodes_created >= 1:
        repo_created = True

      if repo_created:

        # Set Owner
        owner_set = Repositories.setOwner(new_repo['id'], identity, ident_str)

      return new_repo   


  @staticmethod
  def getData(repository_id):

    nodes = []
    result = db.run("MATCH (r:Repository)<-[rel:PART_OF]-(n) WHERE ID(r)={repository_id} RETURN n LIMIT 2", {"repository_id": repository_id})
    
    for data in result:
      nodes.append(data.items()[0][1].properties)

    return nodes 

  @staticmethod
  def getInfo(repository_id):

    repo = {}
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repository_id} RETURN n.url AS url, n.name AS name, n.readme AS readme",
      {"repository_id": repository_id})

    for r in result:
      repo['url'] = r['url']
      repo['name'] = r['name']
      repo['readme'] = r['readme']

    return repo

  @staticmethod
  def delete(repository_id):
  
    del_success = False
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repository_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n", {"repository_id": repository_id})
    summary = result.consume()

    if summary.counters.nodes_deleted >= 1:
      del_success = True

    return del_success

  @staticmethod
  def setOwner(repository_id, identity, ident_str):

    owner_success = False
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repository_id} MATCH (p:Person) WHERE " + ident_str + 
      " MERGE (p)<-[:OWNED_BY]->(n)", {"repository_id": repository_id, "identity": identity})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      owner_success = True

    return owner_success

  @staticmethod
  def getOwner(repository_id):

    owner = {}
    result = db.run("MATCH (n)<-[:OWNED_BY]-(p) WHERE ID(n)={repository_id} RETURN ID(p) AS id, p.name AS name, p.email as email, p.url AS url, " +
      "p.location AS location, p.tagline AS tagline", {"repository_id": repository_id})

    for r in result:
      owner['id'] = r['id']
      owner['name'] = r['name']
      owner['location'] = r['location']
      owner['email'] = r['email']
      owner['url'] = r['url']
      owner['tagline'] = r['tagline']
 
    return owner

  @staticmethod
  def deleteOwner(repository_id, owner_id):

    del_success = False
    result = db.run("START p=node(*) MATCH (p)-[rel:OWNED_BY]->(n) WHERE ID(p)={owner_id} AND ID(n)={repository_id} DELETE rel",
      {"owner_id": owner_id, "repository_id": repository_id})

    summary = result.consume()
    if summary.counters.relationships_deleted >= 1:
      del_success = True

    return del_success

  @staticmethod
  def getInfo(repository_id):
  
    repo = {}
    result = dub.run("MATCH (n:Repository) WHERE ID(n)={repository_id} RETURN n.name AS name, n.url AS url, n.readme AS readme",
      {"repository_id": repository_id})

    for r in result:
      repo['name'] = r['name']
      repo['url'] = r['url']
      repo['readme'] = r['readme']

    return repo

  @staticmethod
  def addCollaborator(repository_id, person_id):

    collab_success = False
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repository_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:COLLABORATES_WITH]->(n)",
      {"repository_id": repository_id, "person_id": person_id})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      collab_success = True

    print "Did we add a collaborator? "
    print collab_success

    return collab_success

  @staticmethod
  def getCollaborators(repository_id):

    people = []
    result = db.run("MATCH (n)<-[:COLLABORATES_WITH]-(p) WHERE ID(n)={repository_id} RETURN p.name AS name, p.email AS email, p.url AS url, " +
      "p.location AS location, p.tagline AS tagline", {"repository_id": repository_id})

    for p in result:
      people.append({
        "name": p['name'],
        "email": p['email'],
        "url": p['url'],
        "location": p['location'],
        "tagline": p['tagline']
      })

    return people

  @staticmethod
  def getUsers(repository_id):
  
    users = []
    result = db.run("MATCH (n)<-[rel:COLLABORATES_WITH|OWNED_BY]-(p) WHERE ID(n)={repository_id} RETURN type(rel) AS role, p.name AS name, ID(p) AS id",
      {"repository_id": repository_id})

    for p in result:
      user_role = ""
      if p['role'] == "COLLABORATES_WITH":
        user_role = "collaborator"
      if p['role'] == "OWNED_BY":
        user_role = "owner"

      users.append({
        "id": p['id'],
        "name": p['name'],
        "role": user_role
      })
    return users

  @staticmethod
  def removeCollaborator(repository_id, person_id):

    del_success = False
    result = db.run("START p=node(*) MATCH (p)-[rel:COLLABORATES_WITH]->(n) WHERE ID(p)={person_id} AND ID(n)={repository_id} DELETE rel",
      {"person_id": person_id, "repository_id": repository_id})

    summary = result.consume()
    if summary.counters.relationships_deleted >= 1:
      del_success = True

    return del_success

  @staticmethod
  def addFollower(repository_id, person_id):
  
    add_success = False
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repository_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:FOLLOWS]->(n)",
      {"repository_id": repository_id, "person_id": person_id})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      add_success = True

    return add_success

  @staticmethod
  def getFollowers(repository_id):

    people = []
    result = db.run("MATCH (n)<-[:FOLLOWS]-(p) WHERE ID(n)={repository_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.location AS location, " +
      "p.tagline AS tagline", {"repository_id": repository_id})

    for p in result:
      people.append({
        "name": p['name'],
        "email": p['email'],
        "url": p['url'],
        "location": p['location'],
        "tagline": p['tagline']
      })

    return people

  @staticmethod
  def removeFollower(repository_id, person_id):
  
    del_success = False
    result = db.run("START p=node(*) MATCH (p)-[rel:FOLLOWS]->(n) WHERE ID(p)={person_id} AND ID(n)={repository_id} DELETE rel",
      {"person_id": person_id, "repository_id": repository_id})

    summary = result.consume()
    if summary.counters.relationship_deleted >= 1:
      del_success = True

    return del_success
