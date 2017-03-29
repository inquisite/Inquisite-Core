import json
from inquisite.db import db
from neo4j.v1 import ResultError

class Repositories:

  # For Now All class methods are going to be static
  def __init__():
    pass 

  
  @staticmethod
  def getData(repository_id):

    nodes = []
    result = db.run("MATCH (r:Repository)<-[rel:PART_OF]-(n) WHERE ID(r)={repository_id} RETURN n LIMIT 2", {"repository_id": repository_id})
    
    for data in result:
      nodes.append(data.items()[0][1].properties)

    return nodes 

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
