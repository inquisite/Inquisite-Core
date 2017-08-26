import datetime
import json
import logging
import time

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_raw_jwt
from passlib.hash import sha256_crypt

from lib.managers.PeopleManager import PeopleManager
from lib.utils.db import db
from lib.utils.requestHelpers import makeResponse
from lib.crossDomain import crossdomain
from lib.exceptions.FindError import FindError
from lib.exceptions.SaveError import SaveError
from lib.exceptions.DbError import DbError
from lib.exceptions.ValidationError import ValidationError
import lib.managers.PeopleManager

people_blueprint = Blueprint('people', __name__)


# People
@people_blueprint.route('/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def peopleList():
    return makeResponse(payload={"people": PeopleManager.getAll()})


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

    if request.method == 'POST':
      identity = int(request.form.get('person_id'))

    person = PeopleManager.getInfo(identity)

    ret = {}
    if person is not None:
      ret['person'] = person

    # If request method is GET, then it's our logged in user, get Repos and repo data too!
    if request.method == 'GET':
      ret['repos'] = PeopleManager.getRepos(identity)

    return makeResponse(payload=ret)


# Add Person
@people_blueprint.route('/people/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def addPerson():
    surname = request.form.get('surname')
    forename = request.form.get('forename')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')
    password = request.form.get('password')

    try:
        ret = PeopleManager.addPerson(forename, surname, location, email, url, tagline, password)
        return makeResponse(payload=ret, message="Added person")
    except DbError as e:
        return makeResponse(error=e)
    except SaveError as e:
        return makeResponse(error=e)
    except FindError as e:
        return makeResponse(error=e)
    except ValidationError as e:
        return makeResponse(error=e)


@people_blueprint.route('/people/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editPerson():
    surname = request.form.get('surname')
    forename = request.form.get('forename')
    location = request.form.get('location')
    email = request.form.get('email')
    url = request.form.get('url')
    tagline = request.form.get('tagline')


    # Get person by auth token 
    current_token = get_raw_jwt()
    jti = current_token['jti']

    # email address
    identity = current_token['identity']
    try:
        return makeResponse(payload=PeopleManager.editPerson(identity, forename, surname, location, email, url, tagline), message="")
    except FindError as e:
        return makeResponse(error=e)
    except ValidationError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)
    except SaveError as e:
        return makeResponse(error=e)
    except Exception as e:
        return makeResponse(error=e)

@people_blueprint.route('/people/<person_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deletePerson(person_id):
    try:
        PeopleManager.deletePerson(person_id)
        return makeResponse(message="Deleted person", payload={})
    except FindError as e:
        return makeResponse(error=e)
    except DbError as e:
        return makeResponse(error=e)

@people_blueprint.route('/people/repos', methods=['GET', 'POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPersonRepos():
    identity = request.form.get('person_id')
    if identity is None:
        current_token = get_raw_jwt()
        identity = current_token['identity']

    try:
        return makeResponse(payload=PeopleManager.getReposForPerson(identity))
    except FindError as e:
        return makeResponse(error=e)


# Get Person by ID
@people_blueprint.route('/people/find', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def findPerson():
    q = request.form.get('q')

    msg = 'No people found'
    ret = {'q': q, 'results': []}

    if q is not None and len(q) > 0:
        people = PeopleManager.find({'surname': q, 'email': q})

        if people is not None:
            msg = 'Success'
            ret['results'] = people

    return makeResponse(payload=ret, message=msg)