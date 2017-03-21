from inquisite.db import db
from neo4j.v1 import ResultError

def getRepositoryByCode(code):
    result = db.run(
        "MATCH (r:Repository {name: {code}}) RETURN ID(r) AS id, r.name AS  name",
        {"code": code})

    ret = {'payload': {}}

    # TODO: clean up payload
    if result:
        for r in result:
            ret['status_code'] = 200
            ret['payload']['repository_id'] = r['id']
            ret['payload']['name'] = r['name']
            break
    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'Could not find repository'

    return ret

def addType(repository_id, name, code, description):

    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': ''
        }
    }

    # TODO validate params


    # TODO: check that repository is owned by current user

    try:
        result = db.run("MATCH (t:SchemaType{code: {code}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t", {"code": code, "repository_id": int(repository_id)}).peek()
        ret['payload']['msg'] = "Type already exists"
    except ResultError as e:
        result = db.run("MATCH (r:Repository) WHERE ID(r) = {repository_id} CREATE (t:SchemaType { name: {name}, code: {code}, description: {description}, storage: 'Graph' })-[:PART_OF]->(r) RETURN r",
                            {"repository_id": int(repository_id),"name": name, "code": code, "description": description})

        # TODO: clean up payload
        if result:
            ret['status_code'] = 200
            ret['payload']['msg'] = "Added type " + name + "//" + str(repository_id)
            ret['payload']['type'] = "xxx"
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong saving new type'


    return ret

def addField(repository_id, typecode, name, code, fieldtype, description):
    # TODO validate params

    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': ''
        }
    }

    # TODO: check that repository is owned by current user

    try:
        result = db.run(
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t",
            {"typecode": typecode, "code": code, "repository_id": int(repository_id)}).peek()
        ret['payload']['msg'] = "Field already exists"
    except ResultError as e:
        result = db.run(
            "MATCH (r:Repository)--(t:SchemaType {code: {typecode}}) WHERE ID(r) = {repository_id} CREATE (f:SchemaField { name: {name}, code: {code}, description: {description}, type: {fieldtype} })-[:PART_OF]->(t) RETURN r",
            {"repository_id": int(repository_id), "name": name, "code": code, "description": description,
             "typecode": typecode, "fieldtype": fieldtype})
        #print result.peek()
        # TODO: check query result

        # TODO: clean up payload
        if result:
            ret['status_code'] = 200
            ret['payload']['msg'] = "Added field " + name + "//" + str(repository_id)
            ret['payload']['type'] = "xxx"
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong saving new field'

    return ret

def addDataToRepo(repository_id, typecode, data):
    ret = {
        'status_code': 200,
        'payload': {
            'msg': 'Success',
            'type': ''
        }
    }

    # TODO: check that repository is owned by current user

    # TODO: verify fields present are valid for this type
    # TODO: validate each field value

    flds = []
    for i in data:
        flds.append(i + ":{" + i + "}")

    data['repository_id'] = int(repository_id)

    result = db.run("CREATE (n:Data" + typecode + " {" + ",".join(flds) + "}) RETURN ID(n) as i", data)
    id = None

    for record in result:
        id = record["i"]

    result = db.run("MATCH (r:Repository), (d:Data" + typecode + ") WHERE ID(d) = " + str(id) + " AND ID(r)= {repository_id} CREATE (r)<-[:PART_OF]-(d)", data)

    if result:
        ret['status_code'] = 200
        ret['payload']['msg'] = "Added data " + typecode + "//" + str(repository_id)
        ret['payload']['type'] = "xxx"
    else:
        ret['status_code'] = 400
        ret['payload']['msg'] = 'Something went wrong saving new data'

    return ret