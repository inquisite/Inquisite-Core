import json
import requests
import collections
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, Blueprint, request, current_app, make_response, session, escape, Response
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import safe_str_cmp
from neo4j.v1 import GraphDatabase, basic_auth
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth


people_blueprint = Blueprint('people', __name__)


config = json.load(open('./config.json'));
driver = GraphDatabase.driver(config['database_url'], auth=basic_auth(config['database_user'],config['database_pass']))
db_session = driver.session()


# People
@people_blueprint.route('/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def peopleList():
    persons = []
    people = db_session.run("MATCH (n:Person) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")
    for p in people:
        persons.append({
            "name": p['name'],
            "location": p['location'],
            "email": p['email'],
            "url": p['url'],
            "tagline": p['tagline']
        })

    resp = (("status", "ok"),
            ("people", persons))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


# Get Person by ID
@people_blueprint.route('/people/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPerson(person_id):
    logging.warning('in getPerson')

    current_user = get_jwt_identity()
    #logging.warning("current_user: " + current_user)
    #logging.warning("person_id: " + person_id)

    result = db_session.run("MATCH (n:Person) WHERE ID(n) = {person_id} RETURN n.name AS name, n.email AS email, n.url AS url, n.location AS location, n.tagline AS tagline", {"person_id": person_id})

    resp = None
    for p in result:
        resp = (("status", "ok"),
                ("name", p['name']),
                ("email", p['email']),
                ("url", p['url']),
                ("location", p['location']),
                ("tagline", p['tagline']))

    if resp is None:
        resp = (("status", "err"),
                ("msg", "Could not find person for that ID"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


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

    # TODO - Enforce password min length / character requirements?
    if password != '' and password is not None:

        password_hash = sha256_crypt.hash(password)
        print "sha256: "
        print password_hash

        ts = time.time()
        created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        result = db_session.run("CREATE (n:Person {url: {url}, name: {name}, email: {email}, location: {location}, tagline: {tagline}, password: {password_hash}, created_on: {created_on}}) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline, ID(n) AS user_id",
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

            resp = (("status", "ok"),
                    ("msg", person['name'] + " added"),
                    ("person", person))
        else:
            resp = (("status", "err"),
                    ("msg", "Something went wrong saving Person"))

    else:
        resp = (("status", "err"),
                ("msg", "User Password is required"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@people_blueprint.route('/people/<person_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editPerson(person_id):
    name = request.form.get('name')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')

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

    print "update list:"
    print update

    update_str = "%s" % ", ".join(map(str, update))

    #print "update string: "
    #print update_str

    if update_str != '' and update_str is not None:
        updated_person = {}
        result = db_session.run("MATCH (p:Person) WHERE ID(p)={person_id} SET " + update_str +
                                " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline", {"person_id": person_id, "name": name, "location": location, "email": email, "url": url, "tagline": tagline})

        if result:
            for p in result:
                updated_person['name'] = p['name']
                updated_person['location'] = p['location']
                updated_person['email'] = p['email']
                updated_person['url'] = p['url']
                updated_person['tagline'] = p['tagline']

            if updated_person != {}:

                resp = (("status", "ok"),
                        ("msg", "Person updated"),
                        ("person", updated_person))

            else:
                resp = (("status", "err"),
                        ("msg", "No person found for that user id"))

        else:
            resp = (("status", "err"),
                    ("msg", "problem updating Person"))

    else:
        resp = (("status", "err"),
                ("msg", "nothing to update"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@people_blueprint.route('/people/<person_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deletePerson(person_id):
    node_deleted = False
    result = db_session.run("MATCH (n:Person) WHERE ID(n)={person_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n", {"person_id": person_id})

    # Check we deleted something
    summary = result.consume()
    if summary.counters.nodes_deleted >= 1:
        node_deleted = True

    if node_deleted:
        resp = (("status", "ok"),
                ("msg", "Peson Deleted Successfully"))
    else:
        resp = (("status", "err"),
                ("msg", "bad user id, nothing was deleted"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@people_blueprint.route('/people/<person_id>/repos', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPersonRepos(person_id):
    result = db_session.run("MATCH (n)<-[:OWNS|FOLLOWS|COLLABORATES_WITH]-(p) WHERE ID(p)={person_id} RETURN n.name AS name, n.readme AS readme, n.url AS url", {"person_id": person_id})

    repos = []
    for item in result:
        repos.append({
            "name": item['name'],
            "readme": item['readme'],
            "url": item['url']
        })

    if result:
        resp = (("status", "ok"),
                ("repos", repos))
    else:
        resp = (("status", "err"),
                ("msg", "error getting repos for Person"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")
