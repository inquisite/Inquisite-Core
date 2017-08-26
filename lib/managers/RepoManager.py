import time
import datetime
from lib.utils.db import db
import datetime
import time

from lib.utils.db import db
from lib.exceptions.ValidationError import ValidationError
from lib.exceptions.DbError import DbError
from lib.exceptions.FindError import FindError


class RepoManager:
  # For Now All class methods are going to be static

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
  def nameCheck(name, repo_id=None, identity=None, ident_str=None):
    if repo_id is not None:
        if identity is not None and ident_str is not None:
            res = db.run("MATCH (n:Repository {name: {name}})--(p:Person) WHERE n.repo_id <> {repo_id} AND " + ident_str + " RETURN n", {"name": name, "repo_id": repo_id, "identity": identity})
        else:
            res = db.run("MATCH (n:Repository {name: {name}}) WHERE n.repo_id <> {repo_id} RETURN n", {"name": name, "repo_id": repo_id})
    else:
        if identity is not None and ident_str is not None:
            res = db.run("MATCH (n:Repository {name: {name}})--(p:Person) WHERE " + ident_str + " RETURN n", {"name": name, "identity": identity})
        else:
            res = db.run("MATCH (n:Repository {name: {name}}) RETURN n", {"name": name})

    if len(list(res)) > 0:
      return False
    else:
      return True    

  @staticmethod
  def create(url, name, readme, identity, ident_str):
      ts = time.time()
      created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

      if url is None or name is None or readme is None:
        raise ValidationError(message="Name, URL and README must be set", context="Repositories.create")

      if RepoManager.nameCheck(name=name, identity=identity, ident_str=ident_str) is False:
        raise ValidationError(message="Name is in use", context="Repositories.create")

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

      if repo_created:  # Set Owner
        owner_set = RepoManager.setOwner(new_repo['id'], identity, ident_str)

      return new_repo   

  @staticmethod
  def edit(repo_id, name, url, readme):
    if url is None or name is None or readme is None:
      raise ValidationError(message="Name, URL and README must be set", context="Repositories.edit")

    if RepoManager.nameCheck(name, repo_id) is False:
      raise ValidationError(message="Name is in use", context="Repositories.edit")

    update = []
    if name is not None:
      update.append("n.name = {name}")

    if url is not None:
      update.append("n.url = {url}")

    if readme is not None:
      update.append("n.readme = {readme}")

    update_str = "%s" % ", ".join(map(str, update))

    if update_str:
      result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} SET " + update_str +
                      " RETURN n.name AS name, n.url AS url, n.readme AS readme, ID(n) as id",
                      {"repo_id": int(repo_id), "name": name, "url": url, "readme": readme})

      updated_repo = {}
      for r in result:
        updated_repo['repo_id'] = r['id']
        updated_repo['name'] = r['name']
        updated_repo['url'] = r['url']
        updated_repo['readme'] = r['readme']

      summary = result.consume()
      if summary.counters.properties_set >= 1:
        return updated_repo

      raise FindError(message="Could not find repository", context="Repositories.edit")

  @staticmethod
  def getData(repo_id):
    RepoManager.validate_repo_id(repo_id)

    nodes = []
    result = db.run("MATCH (r:Repository)--(f:SchemaType)--(n:Data) WHERE ID(r)={repo_id} RETURN n LIMIT 20", {"repo_id": int(repo_id)})
    
    for data in result:
      nodes.append(data.items()[0][1].properties)

    return nodes 

  @staticmethod
  def getInfo(repo_id):
    RepoManager.validate_repo_id(repo_id)

    repo = {}
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} RETURN n.url AS url, n.name AS name, n.readme AS readme",
      {"repo_id": repo_id})

    for r in result:
      repo['url'] = r['url']
      repo['name'] = r['name']
      repo['readme'] = r['readme']

    return repo

  @staticmethod
  def delete(repo_id):
    RepoManager.validate_repo_id(repo_id)

    # TODO: clean up all repo nodes (currently schema and data nodes are not removed)
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n", {"repo_id": repo_id})
    summary = result.consume()

    if summary.counters.nodes_deleted >= 1:
      return True

    raise FindError(message="Could not find repository", context="Repositories.delete")

  @staticmethod
  def setOwner(repo_id, identity, ident_str):
    RepoManager.validate_repo_id(repo_id)

    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE " + ident_str +
      " MERGE (p)<-[:OWNED_BY]->(n)", {"repo_id": repo_id, "identity": identity})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      return True
    else:
      raise FindError(message="Could not find person", context="Repositories.setOwner")

  @staticmethod
  def getOwner(repo_id):
    RepoManager.validate_repo_id(repo_id)

    owner = {}
    result = db.run("MATCH (n)<-[:OWNED_BY]-(p) WHERE ID(n)={repo_id} RETURN ID(p) AS id, p.name AS name, p.email as email, p.url AS url, " +
      "p.location AS location, p.tagline AS tagline", {"repo_id": repo_id})

    for r in result:
      owner['id'] = r['id']
      owner['name'] = r['name']
      owner['location'] = r['location']
      owner['email'] = r['email']
      owner['url'] = r['url']
      owner['tagline'] = r['tagline']
 
    return owner

  @staticmethod
  def deleteOwner(repo_id, owner_id):
    RepoManager.validate_repo_id(repo_id)

    result = db.run("START p=node(*) MATCH (p)-[rel:OWNED_BY]->(n) WHERE ID(p)={owner_id} AND ID(n)={repo_id} DELETE rel",
      {"owner_id": owner_id, "repo_id": repo_id})

    summary = result.consume()
    if summary.counters.relationships_deleted >= 1:
      return True

    raise FindError(message="Could not find person or repository", context="Repositories.deleteOwner")

  @staticmethod
  def getInfo(repo_id):
    RepoManager.validate_repo_id(repo_id)

    repo = {}
    result = dub.run("MATCH (n:Repository) WHERE ID(n)={repo_id} RETURN n.name AS name, n.url AS url, n.readme AS readme",
      {"repo_id": repo_id})

    for r in result:
      repo['name'] = r['name']
      repo['url'] = r['url']
      repo['readme'] = r['readme']

    return repo

  @staticmethod
  def addCollaborator(repo_id, person_id, access="read-only"):
    RepoManager.validate_repo_id(repo_id)

    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[x:COLLABORATES_WITH]->(n) ON CREATE SET x.access = {access}",
      {"repo_id": repo_id, "person_id": person_id, "access": access})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      return True
    raise FindError(message="Already exists", context="Repositories.addCollaborator")

  @staticmethod
  def getCollaborators(repo_id):
    RepoManager.validate_repo_id(repo_id)

    people = []
    result = db.run("MATCH (n)<-[:COLLABORATES_WITH]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, " +
      "p.location AS location, p.tagline AS tagline", {"repo_id": repo_id})

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
  def getUsers(repo_id):
    RepoManager.validate_repo_id(repo_id)

    users = []
    result = db.run("MATCH (n)<-[rel:COLLABORATES_WITH|OWNED_BY]-(p) WHERE ID(n)={repo_id} RETURN type(rel) AS role, p.name AS name, p.email as email, rel.access AS access, ID(p) AS id",
      {"repo_id": repo_id})

    for p in result:
      user_role = ""
      if p['role'] == "COLLABORATES_WITH":
        user_role = "collaborator"
      if p['role'] == "OWNED_BY":
        user_role = "owner"

      users.append({
        "id": p['id'],
        "name": p['name'],
        "email": p['email'],
        "access": p['access'],
        "role": user_role
      })
    return users

  @staticmethod
  def removeCollaborator(repo_id, person_id):
    RepoManager.validate_repo_id(repo_id)

    result = db.run("START p=node(*) MATCH (p)-[rel:COLLABORATES_WITH]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel",
      {"person_id": person_id, "repo_id": repo_id})

    summary = result.consume()
    if summary.counters.relationships_deleted >= 1:
      return True

    raise FindError(message="Could not find person or repository", context="Repositories.removeCollaborator")

  @staticmethod
  def addFollower(repo_id, person_id):
    RepoManager.validate_repo_id(repo_id)

    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:FOLLOWS]->(n)",
      {"repo_id": repo_id, "person_id": person_id})

    summary = result.consume()
    if summary.counters.relationships_created >= 1:
      return True

    raise FindError(message="Could not find person or repository", context="Repositories.addFollower")

  @staticmethod
  def getFollowers(repo_id):
    RepoManager.validate_repo_id(repo_id)

    people = []
    result = db.run("MATCH (n)<-[:FOLLOWS]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.location AS location, " +
      "p.tagline AS tagline", {"repo_id": repo_id})

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
  def removeFollower(repo_id, person_id):
    RepoManager.validate_repo_id(repo_id)

    result = db.run("START p=node(*) MATCH (p)-[rel:FOLLOWS]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel",
      {"person_id": person_id, "repo_id": repo_id})

    summary = result.consume()
    if summary.counters.relationship_deleted >= 1:
      return True

    raise FindError(message="Could not find person", context="Repositories.removeFollower")

  @staticmethod
  def validate_repo_id(repo_id):
    if repo_id is None or repo_id <= 0:
      raise ValidationError(message="Repository id is not set", context="Repositories.validate_repo_id")

    return True