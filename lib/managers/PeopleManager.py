import json

from lib.utils.Db import db
from lib.exceptions.DbError import DbError
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError
from lib.exceptions.ValidationError import ValidationError
from lib.utils.UtilityHelpers import is_number
from passlib.hash import sha256_crypt
import time
import datetime
from validate_email import validate_email
from lib.utils.UtilityHelpers import email_domain_is_allowed
from lib.utils.MailHelpers import send_mail
from api.config import app_config
import lib.managers.RepoManager


class PeopleManager:
  # For Now All class methods are going to be static

  @staticmethod
  def getAll():

    persons = []
    result = db.run("MATCH (p:Person) OPTIONAL MATCH (p)--(r:Repository) RETURN COUNT(r) AS repo_count, ID(p) AS id, p.surname AS surname, p.forename as forename, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline, p.is_admin as is_admin, p.is_disabled as is_disabled, p.nyunetid AS nyunetid ORDER BY p.surname, p.forename")

    for p in result:

      persons.append({
        "id": p['id'],
        "name": str(p['forename']) + " " + str(p['surname']),
        "surname": p['surname'],
        "forename": p['forename'],
        "location": p['location'],
        "email": p['email'],
        "url": p['url'],
        "tagline": p['tagline'],
        "is_admin": p['is_admin'],
        "is_disabled": p['is_disabled'],
        "nyunetid": p['nyunetid'],
        "repo_count": p['repo_count']
      })

    return persons

  @staticmethod
  def getInfo(identity):
    if is_number(identity):
      ident_str = "ID(p)={identity}"
    else:
      ident_str = "p.email={identity}"

    person = {}
    result = db.run("MATCH (p:Person) WHERE " + ident_str + " RETURN ID(p) AS id, p.surname AS surname, p.forename as forename, p.email AS email, " +
      "p.url AS url, p.location AS location, p.tagline AS tagline, p.is_admin AS is_admin, p.is_disabled AS is_disabled, p.nyunetid AS nyunetid", {"identity": identity})

    for p in result:
      repo_count = 0
      repos = db.run("MATCH (r:Repository)--(p:Person) WHERE " + ident_str + " RETURN COUNT(r) AS repo_count", {"identity": identity})
      for r in repos:
        repo_count = r["repo_count"]

      person['id'] = p['id']
      person['name'] = str(p['forename']) + " " + str(p['surname'])
      person['surname'] = p['surname']
      person['forename'] = p['forename']
      person['email'] = p['email']
      person['url'] = p['url']
      person['location'] = p['location']
      person['tagline'] = p['tagline']
      person['is_admin'] = p['is_admin']
      person['is_disabled'] = p['is_disabled']
      person['nyunetid'] = p['nyunetid']
      person['repo_count'] = repo_count

    return person

  @staticmethod
  def getRepoIDs(identity):
    repoIDs = []

    if is_number(identity):
      ident_str = "ID(p)={identity}"
    else:
      ident_str = "p.email={identity}"

    result = db.run("MATCH (n:Repository)<-[x:OWNED_BY|COLLABORATES_WITH]-(p) WHERE " + ident_str + " RETURN ID(n) AS repo_id", {"identity": identity})

    for item in result:
      repoIDs.append(item['repo_id'])

    return repoIDs

  @staticmethod
  def getRepos(identity):
    repos = []

    if is_number(identity):
      ident_str = "ID(p)={identity}"
    else:
      ident_str = "p.email={identity}"

    result = db.run("MATCH (n:Repository)<-[x:OWNED_BY|COLLABORATES_WITH]-(p) WHERE " + ident_str + " RETURN ID(n) AS id, n.name AS name, n.readme AS readme, n.published AS published, n.license AS license, " +
      "n.url AS url, n.created_on AS created_on, n.published_on as published_on, n.featured as featured, x.access AS access", {"identity": identity})

    for item in result:

      owner = lib.managers.RepoManager.RepoManager.getOwner(int(item['id']))
      data  = lib.managers.RepoManager.RepoManager.getData(int(item['id']))
      users = lib.managers.RepoManager.RepoManager.getUsers(int(item['id']))

      repos.append({
        "id": item['id'],
        "name": item['name'],
        "readme": item['readme'],
        "created_on": item['created_on'],
        "published_on": item['published_on'],
        "featured": item['featured'],
        "url": item['url'],
        "data": data,
        "users": users,
        "owner": owner,
        "access": item['access'],
        "published": item['published'],
        "license": item['license'],
        "schema_type_count" : 0,
        "schema_field_count" : 0,
        "data_element_count": 0
      })

    for item in repos:
      result = db.run(
        "MATCH (n:Repository)--(t:SchemaType)--(d:Data) WHERE ID(n) = {repo_id} RETURN count(d) as data_element_count", {"repo_id": int(item['id'])})
      for r in result:
          item['data_element_count'] = r['data_element_count']

      result = db.run(
        "MATCH (n:Repository)--(t:SchemaType)WHERE ID(n) = {repo_id} RETURN count(DISTINCT(t)) as schema_type_count",
        {"repo_id": int(item['id'])})
      for r in result:
        item['schema_type_count'] = r['schema_type_count']

      result = db.run(
        "MATCH (n:Repository)--(t:SchemaType)--(f:SchemaField) WHERE ID(n) = {repo_id} RETURN count(DISTINCT(t)) as schema_type_count, count(DISTINCT(f)) as schema_field_count",
        {"repo_id": int(item['id'])})
      for r in result:
        item['schema_field_count'] = r['schema_field_count']
    return repos


  @staticmethod
  def find(params):
    people = []
    criteria = []

    if ('surname' in params) and (params['surname']) and len(params['surname']) > 0:
      params['surname'] = params['surname'].lower()
      criteria.append("lower(p.surname) CONTAINS {surname}")
    if ('forename' in params) and (params['forename']) and len(params['forename']) > 0:
      params['forename'] = params['forename'].lower()
      criteria.append("lower(p.forename) CONTAINS {forename}")
    if ('email' in params) and (params['email']) and len(params['email']) > 0:
      params['email'] = params['email'].lower()
      criteria.append("lower(p.email) STARTS WITH {email}")

    if len(criteria) == 0:
      return None


    result = db.run("MATCH (p:Person) WHERE " + " OR ".join(criteria) + " RETURN ID(p) AS id, p.surname AS surname, p.forename AS forename, p.email AS email, " +
                    "p.url AS url, p.location AS location, p.tagline AS tagline",
                    params)

    for p in result:
      r = {'name': str(p['forename']) + ' ' + p['surname'] }
      for f in ['id', 'surname', 'forename', 'email', 'url', 'location', 'tagline']:
        r[f] = p[f]
      people.append(r)

    return people

  @staticmethod
  def addPerson(forename, surname, location, email, nyunetid, url, tagline, password):
    if validate_email(email, verify=False) is False:
      raise SaveError(message="Email address is invalid", context="People.addPerson")
    if email_domain_is_allowed(email) is False:
      raise SaveError(message="You cannot register with this email address", context="People.addPerson")

    # TODO - Enforce password more complex password requirements?
    if password is not None and (len(password) >= 6):
      password_hash = sha256_crypt.hash(password)

      ts = time.time()
      created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

      try:
        result = db.run("MATCH (n:Person{email: {email}}) RETURN ID(n) as id, n.surname as surname, n.forename AS forename, n.email as email, n.nyunetid as nyunetid", {"email": email}).peek()
      except Exception as e:
        raise DbError(message="Could not look up user", context="People.addPerson", dberror=e.message)

      if result:
        raise SaveError(message="User already exists with this email address", context="People.addPerson")
        # return {
        #   "exists": True,
        #   "user_id": result['id'],
        #   "surname": result['surname'],
        #   "forename": result['forename'],
        #   "name": str(result['forename']) + " " + str(result['surname']),
        #   "email": result['email'],
        #   "nyunetid": result['nyunetid']
        # }
      else:
        try:
          result = db.run(
            "CREATE (n:Person {url: {url}, surname: {surname}, forename: {forename}, email: {email}, location: {location}, tagline: {tagline}, nyunetid: {nyunetid}, is_disabled: 0, is_admin: 0," +
            "password: {password_hash}, created_on: {created_on}, prefs: ''})" +
            " RETURN n.forename AS forename, n.surname AS surname, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline, n.nyunetid as nyunetid, ID(n) AS user_id",
            {"url": url, "surname": surname, "forename" : forename, "email": email, "location": location, "tagline": tagline, "nyunetid": nyunetid,
             "password_hash": password_hash, "created_on": created_on})
        except Exception as e:
          raise DbError(message="Could not create user", context="People.addPerson", dberror=e.message)

        if result:
          person = {}
          for p in result:
            person['surname'] = p['surname']
            person['forename'] = p['forename']
            person['name'] = str(p['forename']) + " " +  str(p['surname'])
            person['location'] = p['location']
            person['email'] = p['email']
            person['nyunetid'] = p['nyunetid']
            person['url'] = p['url']
            person['tagline'] = p['tagline']
            person['user_id'] = p['user_id']

            send_mail(p['email'], None, "Registration notification", "registration",
                      {"email": p['email'],
                       "login_url": app_config["base_url"]})
            return person

        else:
          raise SaveError(message="Could not add person", context="People.addPerson")

    raise SaveError(message="Password must be at least six characters in length", context="People.addPerson")

  @staticmethod
  def editPerson(identity, forename, surname, location, email, url, tagline, is_disabled, nyunetid):
    if is_number(identity):
      ident_str = "ID(p)={identity}"
      identity = int(identity)
    else:
      ident_str = "p.email={identity}"

    update = []
    if forename is not None:
        update.append("p.forename = {forename}")

    if surname is not None:
        update.append("p.surname = {surname}")

    if location is not None:
        update.append("p.location = {location}")

    if email is not None:
        update.append("p.email = {email}")

    if url is not None:
        update.append("p.url = {url}")

    if tagline is not None:
        update.append("p.tagline = {tagline}")

    if nyunetid is not None:
        update.append("p.nyunetid = {nyunetid}")

    if is_disabled is not None:
        print is_disabled
        try:
          is_disabled = int(is_disabled)
          if is_disabled <> 0:
              is_disabled = 1
          update.append("p.is_disabled = {is_disabled}")
        except:
          pass

    update_str = "%s" % ", ".join(map(str, update))


    if update_str != '' and update_str is not None:
        result = db.run("MATCH (p:Person) WHERE " + ident_str + " SET " + update_str +
          " RETURN p.forename AS forename, p.surname AS surname, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline, p.is_disabled AS is_disabled, p.nyunetid AS nyunetid",
          {"identity": identity, "forename": forename, "surname": surname, "location": location, "email": email, "url": url, "tagline": tagline, "is_disabled": is_disabled, "nyunetid": nyunetid})

        if result:
            updated_person = {}
            for p in result:
                updated_person['forename'] = p['forename']
                updated_person['surname'] = p['surname']
                updated_person['name'] = str(p['forename']) + " " + str(p['surname'])
                updated_person['location'] = p['location']
                updated_person['email'] = p['email']
                updated_person['url'] = p['url']
                updated_person['tagline'] = p['tagline']
                updated_person['is_disabled'] = p['is_disabled']
                updated_person['nyunetid'] = p['nyunetid']

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
    repos = PeopleManager.getRepos(identity)
    user = PeopleManager.getInfo(identity)

    if repos is not None:
      return {"repos": repos, "userinfo": user}

    raise FindError(message="Could not find person", context="People.getReposForPerson")


  #
  # INTERNAL ONLY
  # Check if a user has permission to edit/contribute to a repository
  # This should prevent users from using their tokens to edit others repos
  # which seems to be possible currently
  @staticmethod
  def checkRepoPermissions(user_name, repo_id):
    repo_list = PeopleManager.getRepoIDs(user_name)
    print repo_list, repo_id
    try:
        repo_id = int(repo_id)
    except:
        raise FindError(message="Need integer repo_id", context="People.checkRepoPermissions")
    if repo_id in repo_list:
      return True
    return False
