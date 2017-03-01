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
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth
from inquisite.db import db
from neo4j.v1 import ResultError


repositories_blueprint = Blueprint('repositories', __name__)


# Repositories
@repositories_blueprint.route('/repositories', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def repoList():
    repos = []
    result = db.run("MATCH (n:Repository) RETURN n.url AS url, n.name AS name, n.readme AS readme")
    for r in result:
        repos.append({
            "name": r['name'],
            "url": r['url'],
            "readme": r['readme']
        })

    resp = (("status", "ok"),
            ("repos", repos))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepo(repo_id):
    repo = {}
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} RETURN n.url AS url, n.name AS name, n.readme AS readme", {"repo_id": repo_id})
    for r in result:
        repo['url'] = r['url']
        repo['name'] = r['name']
        repo['readme'] = r['readme']

    if repo:
        resp = (("status", "ok"),
                ("repo", repo))
    else:
        resp = (("status", "err"),
                ("msg", "No repo for that repo_id found"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepo():
    url = request.form.get('url')
    name = request.form.get('name')
    readme = request.form.get('readme')

    if url is not None and name is not None and readme is not None:
        try:
           db.run("MATCH (n:Repository {name: {name}}) RETURN n", {"name": name}).peek()
           resp = (("status", "err"),
                   ("msg", "Repository with name already exists"))
        except ResultError as e:
            ts = time.time()
            created_on = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            new_repo = {}
            result = db.run("CREATE (n:Repository {url: {url}, name: {name}, readme: {readme}, created_on: {created_on}}) RETURN n.url AS url, n.name AS name, n.readme AS readme, ID(n) AS repo_id", {"url": url, "name": name, "readme": readme, "created_on": created_on})

            for r in result:
                new_repo['repo_id'] = r['repo_id']
                new_repo['url'] = r['url']
                new_repo['name'] = r['name']
                new_repo['readme'] = r['readme']

            node_created = False
            summary = result.consume()
            if summary.counters.nodes_created >= 1:
                node_created = True

            if node_created:
                resp = (("status", "ok"),
                        ("repo", new_repo),
                        ("msg", "Created Repo"))
            else:
                resp = (("status", "err"),
                        ("msg", "problem creating repo"))
    else:
        resp = (("status", "err"),
                ("msg", "Required fields are missing"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editRepo(repo_id):
    url = request.form.get('url')
    name = request.form.get('name')
    readme = request.form.get('readme')

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
                                " RETURN n.name AS name, n.url AS url, n.readme AS readme", {"repo_id": repo_id, "name": name, "url": url, "readme": readme})

        updated_repo = {}
        for r in result:
            updated_repo['name'] = r['name']
            updated_repo['url'] = r['url']
            updated_repo['readme'] = r['readme']

        node_updated = False
        summary = result.consume()
        if summary.counters.properties_set >= 1:
            node_updated = True

        if node_updated:
            resp = (("status", "ok"),
                    ("msg", "Repository updated"),
                    ("repo", updated_repo))
        else:
            resp = (("status", "err"),
                    ("msg", "Problem updating Repo"))

    else:
        resp = (("status", "err"),
                ("msg", "Nothing to update"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepo(repo_id):
    result = db.run("MATCH (n:Repository) WHERE ID(n)={repo_id} OPTIONAL MATCH (n)-[r]-() DELETE r,n", {"repo_id": repo_id})
    summary = result.consume()

    node_deleted = False
    if summary.counters.nodes_deleted >= 1:
        node_deleted = True

    if node_deleted:
        resp = (("status", "ok"),
                ("msg", "Repo deleted"))
    else:
        resp = (("status", "err"),
                ("msg", "Problem deleting repo"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/set_owner/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setRepoOwner(repo_id, person_id):
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)<-[:OWNED_BY]->(n)", {"repo_id": repo_id, "person_id": person_id})
    summary = result.consume()

    rel_created = False
    if summary.counters.relationships_created >= 1:
        rel_created = True

    if rel_created:
        resp = (("status", "ok"),
                ("msg", "Repository owner set successfully"))
    else:
        resp = (("status", "err"),
                ("msg", "There was a problem, no owner set"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/owner', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoOwner(repo_id):
    owner = {}
    result = db.run("MATCH (n)<-[:OWNED_BY]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline", {"repo_id": repo_id})
    for r in result:
        owner['name'] = r['name']
        owner['location'] = r['location']
        owner['email'] = r['email']
        owner['url'] = r['url']
        owner['tagline'] = r['tagline']

    if result:
        resp = (("status", "ok"),
                ("owner", owner))
    else:
        resp = (("status", "err"),
                ("msg", "could not retreive owner"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/remove_owner/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepoOwner(repo_id, person_id):
    result = db.run(
        "START p=node(*) MATCH (p)-[rel:OWNED_BY]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel", {"person_id": person_id, "repo_id": repo_id})
    summary = result.consume()

    rel_deleted = False
    if summary.counters.relationships_deleted >= 1:
        rel_deleted = True

    if rel_deleted:
        resp = (("status", "ok"),
                ("msg", "Repo Owner removed successfully"))
    else:
        resp = (("status", "err"),
                ("msg", "There was a problem, Repo owner was not removed"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoInfo(repo_id):
    repo = {}
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} RETURN n.name AS name, n.url AS url, n.readme AS readme", {"repo_id": repo_id})
    for r in result:
        repo['name'] = r['name']
        repo['url'] = r['url']
        repo['readme'] = r['readme']

    if result:
        resp = (("status", "ok"),
                ("repo", repo))
    else:
        resp = (("status", "err"),
                ("msg", "could not return repo info"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/add_collaborator/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoCollab(repo_id, person_id):
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:COLLABORATES_WITH]->(n)", {"repo_id": repo_id, "person_id": person_id})

    if result:
        resp = (("status", "ok"),
                ("msg", "Collaborator Added"))
    else:
        resp = (("status", "err"),
                ("msg", "Problem adding Collaborator"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/collaborators', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoCollabs(repo_id):
    people = []
    result = db.run("MATCH (n)<-[:COLLABORATES_WITH]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline", {"repo_id": repo_id})

    for p in result:
        people.append({
            "name": p['name'],
            "email": p['email'],
            "url": p['url'],
            "location": p['location'],
            "tagline": p['tagline']
        })

    if people:
        resp = (("status", "ok"),
                ("collaborators", people))
    else:
        resp = (("status", "err"),
                ("msg", "There was a problem returning collaborators"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/remove_collaborator/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoCollab(repo_id, person_id):
    result = db.run(
        "START p=node(*) MATCH (p)-[rel:COLLABORATES_WITH]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel", {"person_id": person_id, "repo_id": repo_id})
    if result:
        resp = (("status", "ok"),
                ("msg", "Collaborator removed"))
    else:
        resp = (("status", "err"),
                ("msg", "Problem removing collaborator"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/add_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoFollower(repo_id, person_id):
    result = db.run(
        "MATCH (n:Repository) WHERE ID(n)={repo_id} MATCH (p:Person) WHERE ID(p)={person_id} MERGE (p)-[:FOLLOWS]->(n)", {"repo_id": repo_id, "person_id": person_id})
    if result:
        resp = (("status", "ok"),
                ("msg", "Folower Added"))
    else:
        resp = (("status", "err"),
                ("msg", "Problem adding follower"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/followers', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def listRepoFollowers(repo_id):
    people = []
    result = db.run("MATCH (n)<-[:FOLLOWS]-(p) WHERE ID(n)={repo_id} RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline", {"repo_id": repo_id})

    for p in result:
        people.append({
            "name": p['name'],
            "email": p['email'],
            "url": p['url'],
            "location": p['location'],
            "tagline": p['tagline']
        })

    if people:
        resp = (("status", "ok"),
                ("followers", people))
    else:
        resp = (("status", "err"),
                ("msg", "There was a problem returning followers"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


@repositories_blueprint.route('/repositories/<repo_id>/remove_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoFollower(repo_id, person_id):
    result = db.run(
        "START p=node(*) MATCH (p)-[rel:FOLLOWS]->(n) WHERE ID(p)={person_id} AND ID(n)={repo_id} DELETE rel", {"person_id": person_id, "repo_id": repo_id})
    if result:
        resp = (("status", "ok"),
                ("msg", "Follower Removed"))
    else:
        resp = (("status", "err"),
                ("msg", "Problem removing follower"))

    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


# TODO: Define Repo / Data Sheet(node) relationships
@repositories_blueprint.route('/repositories/<repo_id>/add_data_node', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoData(repo_id):
    result = db.run()


@repositories_blueprint.route('/repositories/<repo_id>/query', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def queryRepo(repo_id):
    result = db.run()


@repositories_blueprint.route('/repositories/<repo_id>/get_all_data', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoData(repo_id):
    result = db.run()


@repositories_blueprint.route('/repositories/<repo_id>/set_entry_point', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setEntryPoint(repo_id):
    result = db.run()
