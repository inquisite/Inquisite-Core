import requests
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, Blueprint, request, current_app, make_response, session, escape
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_raw_jwt, revoke_token
from werkzeug.security import safe_str_cmp
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth
from inquisite.db import db
from neo4j.v1 import ResultError

from response_handler import response_handler

people_blueprint = Blueprint('people', __name__)


# People
@people_blueprint.route('/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def peopleList():

    ret = {
      'status_code': 200,
      'payload': {
        'people': []
      }
    }

    persons = []
    people = db.run("MATCH (n:Person) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")
    for p in people:
        persons.append({
            "name": p['name'],
            "location": p['location'],
            "email": p['email'],
            "url": p['url'],
            "tagline": p['tagline']
        })

    ret['payload']['people'] = persons
    
    return response_handler(ret)


# Get Person by ID
@people_blueprint.route('/people/info', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPerson():
    logging.warning('in getPerson')

    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']


    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Could not find person for that ID',
        'person': {}
      }
    }

    current_user = get_jwt_identity()
    
    print "current_user: " + str(current_user)
    print "identity: " + str(identity)



    result = db.run("MATCH (n:Person) WHERE n.email={identity} RETURN n.name AS name, n.email AS email, n.url AS url, n.location AS location, n.tagline AS tagline",
      {"identity": identity})

    for p in result:
        ret['status_code'] = 200
        ret['payload']['msg'] = 'Success'
        ret['payload']['person'] = {'name': p['name'], 'email': p['email'], 'url': p['url'], 'location': p['location'], 'tagline': p['tagline']}

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
      'status_code': 422,
      'payload': {
        'msg': 'Password must be at least 6 characters',
        'person': {}
      }
    }

    # TODO - Enforce password more complex password requirements?
    if password is not None and (len(password) >= 6):

        print "Password requirements met"

        password_hash = sha256_crypt.hash(password)

        ts = time.time()
        created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        try:
            result = db.run("MATCH (n:Person{email: {email}}) RETURN n", {"email": email}).peek()
            ret['payload']['msg'] = "User already exists"
        except ResultError as e:
            result = db.run("CREATE (n:Person {url: {url}, name: {name}, email: {email}, location: {location}, tagline: {tagline}, password: {password_hash}, created_on: {created_on}}) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline, ID(n) AS user_id",
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

@people_blueprint.route('/people/<person_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editPerson(person_id):
    name = request.form.get('name')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')

    ret = {
      'status_code': 422,
      'payload': {
        'msg': 'Nothing to update',
        'person': {}
      } 
    } 

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

    update_str = "%s" % ", ".join(map(str, update))

    if update_str != '' and update_str is not None:
        updated_person = {}
        result = db.run("MATCH (p:Person) WHERE ID(p)={person_id} SET " + update_str +
                                " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline", {"person_id": person_id, "name": name, "location": location, "email": email, "url": url, "tagline": tagline})

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

@people_blueprint.route('/people/repos', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPersonRepos():

    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']

    ret = {
      'status_code': 400,
      'payload': {
        'msg': 'Error getting repos for Person',
        'repos': {}
      } 
    }

    result = db.run("MATCH (n)<-[:OWNS|OWNED_BY|FOLLOWS|COLLABORATES_WITH]-(p) WHERE p.email={identity} RETURN ID(n) AS id, n.name AS name, n.readme AS readme, n.url AS url", 
      {"identity": identity})

    repos = []
    for item in result:
        repos.append({
            "id": item['id'],
            "name": item['name'],
            "readme": item['readme'],
            "url": item['url']
        })

    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = "Success"
        ret['payload']['repos'] = repos

    return response_handler(ret)
