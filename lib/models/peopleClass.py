import json

from lib.models.repositoriesClass import Repositories
from lib.utils.db import db
from lib.exceptions.DbError import DbError
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError
from lib.exceptions.ValidationError import ValidationError
from lib.utils.utilityHelpers import is_number
from passlib.hash import sha256_crypt
import time
import datetime


class People:
  # For Now All class methods are going to be static

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
  def getInfo(identity):
    if is_number(identity):
      ident_str = "ID(p)={identity}"
    else:
      ident_str = "p.email={identity}"

    person = {}
    result = db.run("MATCH (p:Person) WHERE " + ident_str + " RETURN ID(p) AS id, p.name AS name, p.email AS email, " +
      "p.url AS url, p.location AS location, p.tagline AS tagline, p.prefs AS prefs", {"identity": identity})

    for p in result:
      #prefs = {}
      #if (p['prefs'] != None):
      #  try:
      #    prefs = json.loads(p['prefs'])
      #  except:
      #    prefs = {}

      person['id'] = p['id']
      person['name'] = p['name']
      person['email'] = p['email']
      person['url'] = p['url']
      person['location'] = p['location']
      person['tagline'] = p['tagline']
      #person['prefs'] = prefs
    
    return person

  @staticmethod
  def getRepos(identity):
    repos = []

    if is_number(identity):
      ident_str = "ID(p)={identity}"
    else:
      ident_str = "p.email={identity}"

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

  @staticmethod
  def addPerson(name, location, email, url, tagline, password):
    # TODO - Enforce password more complex password requirements?
    if password is not None and (len(password) >= 6):
      password_hash = sha256_crypt.hash(password)

      ts = time.time()
      created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

      try:
        result = db.run("MATCH (n:Person{email: {email}}) RETURN ID(n) as id, n.name as name, n.email as email", {"email": email}).peek()
      except Exception as e:
        raise DbError(message="Could not look up user", context="People.addPerson", dberror=e.message)

      if result:
        return {
          "exists": True,
          "user_id": result['id'],
          "name": result['name'],
          "email": result['email']
        }
      else:
        try:
          result = db.run(
            "CREATE (n:Person {url: {url}, name: {name}, email: {email}, location: {location}, tagline: {tagline}, " +
            "password: {password_hash}, created_on: {created_on}, prefs: ''})" +
            " RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline, ID(n) AS user_id",
            {"url": url, "name": name, "email": email, "location": location, "tagline": tagline,
             "password_hash": password_hash, "created_on": created_on})
        except Exception as e:
          raise DbError(message="Could not create user", context="People.addPerson", dberror=e.message)

        if result:
          person = {}
          for p in result:
            person['name'] = p['name']
            person['location'] = p['location']
            person['email'] = p['email']
            person['url'] = p['url']
            person['tagline'] = p['tagline']
            person['user_id'] = p['user_id']
            return person

        else:
          raise SaveError(message="Could not add person", context="People.addPerson")


  @staticmethod
  def editPerson(identity, name, location, email, url, tagline):
    update = []
    if name is not None:
        update.append("p.name = {name}")

    if location is not None:
        update.append("p.location = {location}")

    if email is not None:
        update.append("p.email = {email}")

    if url is not None:
        update.append("p.url = {url}")

    if tagline is not None:
        update.append("p.tagline = {tagline}")

    #if prefs is not None:
    #    prefs = json.dumps(prefs)
    #    update.append("p.prefs = {prefs}")

    update_str = "%s" % ", ".join(map(str, update))


    if update_str != '' and update_str is not None:
        updated_person = None
        result = db.run("MATCH (p:Person) WHERE p.email={identity} SET " + update_str +
          " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline",
          {"identity": identity, "name": name, "location": location, "email": email, "url": url, "tagline": tagline}) # "prefs": prefs})

        if result:
            updated_person = {}
            for p in result:
                updated_person['name'] = p['name']
                updated_person['location'] = p['location']
                updated_person['email'] = p['email']
                updated_person['url'] = p['url']
                updated_person['tagline'] = p['tagline']

            if updated_person is not None:
                return updated_person
            else:
                raise FindError(message="Person does not exist", context="People.editPerson")

        else:
          raise DbError(message="Could not update person", context="People.editPerson", dberror="")
    else:
      raise ValidationError(message="Nothing to update", context="People.editPerson")

  @staticmethod
  def deletePerson(person_id):
    try:
      result = db.run("MATCH (n:Person) WHERE ID(n)={person_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n",
                      {"person_id": person_id})
    except Exception as e:
      raise DbError(message="Could not delete person", context="People.deletePerson", dberror=e.message)

      # Check that we deleted something
    summary = result.consume()
    if summary.counters.nodes_deleted >= 1:
      return True

    raise FindError(message="Could not find person", context="People.deletePerson")

  @staticmethod
  def getReposForPerson(identity):
    repos = People.getRepos(identity)
    user = People.getInfo(identity)

    if repos is not None:
      return {"repos": repos, "userinfo": user}

    raise FindError(message="Could not find person", context="People.getReposForPerson")