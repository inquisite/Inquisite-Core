import datetime
import json
import logging
import time

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_raw_jwt
from passlib.hash import sha256_crypt

from lib.models.peopleClass import People
from lib.utils.db import db
from response_handler import response_handler
from simpleCrossDomain import crossdomain

people_blueprint = Blueprint('people', __name__)


# People
@people_blueprint.route('/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def peopleList():

    persons = People.getAll()

    ret = {
      'status_code': 200,
      'payload': {
        'people': persons
      }
    }
    
    return response_handler(ret)


# Get Person by ID
@people_blueprint.route('/people/info', methods=['GET', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPerson():

    if request.method == 'GET':
      # Get person by auth token 
      current_token = get_raw_jwt()
      jti = current_token['jti']

      # email address
      identity = current_token['identity']
      ident_str = "p.email={identity}"

    if request.method == 'POST':
      identity = int(request.form.get('person_id'))
      ident_str = "ID(p)={identity}"


    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Could not find person for that ID',
        'person': {},
        'repos': []
      }
    }
    
    person = People.getInfo(identity, ident_str)

    if person is not None:
      ret['status_code'] = 200
      ret['payload']['msg'] = 'Success'
      ret['payload']['person'] = person    

    # If request method is GET, then it's our logged in user, get Repos and repo data too!
    if request.method == 'GET':
      ret['payload']['repos'] = People.getRepos(identity, ident_str)  

   

    return response_handler(ret)


# Add Person
@people_blueprint.route('/people/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def addPerson():
    logging.warning("in addPerson")

    name = request.form.get('name')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')
    password = request.form.get('password')

    ret = {
      'status_code': 200,
      'payload': {
        'msg': 'Password must be at least 6 characters',
        'person': {}
      }
    }

    # TODO - Enforce password more complex password requirements?
    if password is not None and (len(password) >= 6):

        password_hash = sha256_crypt.hash(password)

        ts = time.time()
        created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        result = db.run("MATCH (n:Person{email: {email}}) RETURN n", {"email": email}).peek()
        if result:
            ret['payload']['msg'] = "User already exists"
        else:
            result = db.run(
              "CREATE (n:Person {url: {url}, name: {name}, email: {email}, location: {location}, tagline: {tagline}, " +
              "password: {password_hash}, created_on: {created_on}, prefs: ''})" +
              " RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline, ID(n) AS user_id",
              {"url": url, "name": name, "email": email, "location": location, "tagline": tagline, "password_hash": password_hash, "created_on": created_on})

            if result:
                person = {}
                for p in result:
                    person['name'] = p['name']
                    person['location'] = p['location']
                    person['email'] = p['email']
                    person['url'] = p['url']
                    person['tagline'] = p['tagline']
                    person['user_id'] = p['user_id']

                ret['status_code'] = 200
                ret['payload']['msg'] = person['name'] + " added"
                ret['payload']['person'] = person
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong saving new person'


    return response_handler(ret)

@people_blueprint.route('/people/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editPerson():
    name = request.form.get('name')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')
    prefs = request.form.get('prefs')

    ret = {
      'status_code': 422,
      'payload': {
        'msg': 'Nothing to update',
        'person': {}
      } 
    } 

    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']


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

    if prefs is not None:
        prefs = json.dumps(prefs)
        update.append("p.prefs = {prefs}")

    update_str = "%s" % ", ".join(map(str, update))


    # TODO: Add User Preferences serialized object 
    if update_str != '' and update_str is not None:
        updated_person = {}
        result = db.run("MATCH (p:Person) WHERE p.email={identity} SET " + update_str +
          " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline", 
          {"identity": identity, "name": name, "location": location, "email": email, "url": url, "tagline": tagline, "prefs": prefs})

        if result:
            for p in result:
                updated_person['name'] = p['name']
                updated_person['location'] = p['location']
                updated_person['email'] = p['email']
                updated_person['url'] = p['url']
                updated_person['tagline'] = p['tagline']

            if updated_person != {}:
                ret['status_code'] = 200
                ret['payload']['msg'] = 'Person updated'
                ret['payload']['person'] = updated_person
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'No person found'

        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Problem updating Person'


    return response_handler(ret)

@people_blueprint.route('/people/<person_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deletePerson(person_id):

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'There was a problem deleting person'
      }
    }

    node_deleted = False
    result = db.run("MATCH (n:Person) WHERE ID(n)={person_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n", {"person_id": person_id})

    # Check we deleted something
    summary = result.consume()
    if summary.counters.nodes_deleted >= 1:
        node_deleted = True

    if node_deleted:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Person deleted successfully'

    return response_handler(ret)

@people_blueprint.route('/people/repos', methods=['GET', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPersonRepos():

    if request.method == 'GET':
      # Get person by auth token 
      current_token = get_raw_jwt()
      jti = current_token['jti']

      # email address
      identity = current_token['identity']
      ident_str = "p.email={identity}"

    if request.method == 'POST':
      identity = int(request.form.get('person_id'))
      ident_str = "ID(p)={identity}"

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Error getting repos for Person',
        'repos': {}
      } 
    }

    repos = People.getRepos(identity, ident_str)
    user = People.getInfo(identity, ident_str)

    if repos is not None:
        ret['status_code'] = 200
        ret['payload']['msg'] = "Success"
        ret['payload']['repos'] = repos
        ret['payload']['userinfo'] = user

    return response_handler(ret)


# Get Person by ID
@people_blueprint.route('/people/find', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def findPerson():
    q = request.form.get('q')
    ret = {
        'status_code': 200,
        'payload': {'msg': 'No people found', 'q': q, 'results': []}
    }

    if q is not None and len(q) > 0:
        people = People.find({'name': q, 'email': q})

        if people is not None:
            ret['status_code'] = 200
            ret['payload']['msg'] = 'Success'
            ret['payload']['results'] = people

    return response_handler(ret)