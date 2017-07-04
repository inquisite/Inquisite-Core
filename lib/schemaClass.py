from inquisite.db import db
import re

class Schema:
    FieldTypes = ['TEXT', 'INT', 'FLOAT', 'DATERANGE', 'GEOREF']


    # For now All class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
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

    # Get list of data types for repository
    @staticmethod
    def getTypes(repository_id):

        ret = {
            'status_code': 200,
            'payload': {
                'msg': 'Success',
                'types': []
            }
        }

        # TODO validate params


        # TODO: check that repository is owned by current user

        result = db.run("MATCH (t:SchemaType)--(r:Repository) WHERE ID(r) = {repository_id}  RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"repository_id": int(repository_id)})

        if result:
            typelist = []
            for r in result:
                t = { 'id': str(r['id']), 'name': r['name'], 'code': r['code'], 'description': r['description']}
                # get fields
                t['fields'] = Schema.getFieldsForType(r['id'])

                typelist.append(t)
            ret['payload']['types'] = typelist

        return ret
    @staticmethod
    def getFieldsForType(type_id):
        # TODO validate params


        # TODO: check that repository is owned by current user

        result = db.run(
            "MATCH (f:SchemaField)--(t:SchemaType) WHERE ID(t) = {type_id}  RETURN ID(f) as id, f.name as name, f.code as code, f.type as type, f.description as description",
            {"type_id": int(type_id)})

        fieldlist = []
        if result:
            for r in result:
                t = {'id': str(r['id']), 'name': r['name'], 'code': r['code'], 'description': r['description'], 'type': r['type']}

                fieldlist.append(t)

        return fieldlist

    @staticmethod
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

        result = db.run("MATCH (t:SchemaType{code: {code}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t", {"code": code, "repository_id": int(repository_id)}).peek()
        if result is not None and len(list(result)):
            ret['payload']['msg'] = "Type already exists"
        else:
            result = db.run("MATCH (r:Repository) WHERE ID(r) = {repository_id} CREATE (t:SchemaType { name: {name}, code: {code}, description: {description}, storage: 'Graph' })-[:PART_OF]->(r) RETURN ID(t) as id",
                            {"repository_id": int(repository_id),"name": name, "code": code, "description": description})

            # TODO: clean up payload
            if result:
                for r in result:
                    ret['status_code'] = 200
                    ret['payload']['msg'] = "Added type " + name + "//" + str(repository_id)
                    ret['payload']['type'] = {
                        "id": r['id'],
                        "name": name,
                        "code": code,
                        "description": description
                    }
                    break
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong saving new type'


        return ret

    @staticmethod
    def editType(repository_id, type_id, name, code, description):

        ret = {
            'status_code': 200,
            'payload': {
                'msg': 'Success',
                'type': ''
            }
        }

        # TODO validate params

        # TODO: check that repository is owned by current user


        result = db.run(
            "MATCH (r:Repository)--(t:SchemaType) WHERE ID(r) = {repository_id} AND ID(t) = {type_id} SET t.name = {name}, t.code = {code}, t.description = {description} RETURN ID(t) AS id",
            {"repository_id": int(repository_id), "type_id": int(type_id), "name": name, "code": code, "description": description})

        # TODO: clean up payload
        if result:
            for r in result:
                ret['payload']['foo'] = 'zzz'
                ret['status_code'] = 200
                ret['payload']['msg'] = "Edited type " + name
                ret['payload']['type'] = {
                    "id": r['id'],
                    "name": name,
                    "code": code,
                    "description": description
                }
                break
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong editing type'

        return ret

    @staticmethod
    def deleteType(repository_id, type_id):

        ret = {
            'status_code': 200,
            'payload': {
                'msg': 'Success'
            }
        }

        # TODO validate params


        # TODO: check that repository is owned by current user

        result = db.run("MATCH (t:SchemaType)-[x]-(r:Repository) WHERE ID(r) = {repository_id} AND ID(t) = {type_id} optional match (f:SchemaField)--(t) DELETE x,t,f",
                        {"type_id": int(type_id), "repository_id": int(repository_id)})
        if result is not None:
            ret['status_code'] = 200
            ret['payload']['msg'] = "Deleted type " + str(type_id)
            ret['payload']['repository_id'] =  repository_id
            ret['payload']['type_id'] = type_id
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong deleting type'

        return ret

    @staticmethod
    def addField(repository_id, typecode, name, code, fieldtype, description):
        # TODO validate params

        ret = {
            'status_code': 200,
            'payload': {
                'msg': 'Success',
                'type': ''
            }
        }

        # Check field type
        if fieldtype not in Schema.FieldTypes:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Invalid field type'
            return ret


        # TODO: check that repository is owned by current user

        result = db.run(
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t",
            {"typecode": typecode, "code": code, "repository_id": int(repository_id)}).peek()
        if len(list(result)) > 0:
            ret['payload']['msg'] = "Field already exists"
        else:
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

    @staticmethod
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
        for i in data.keys():
            if (i == '_ID'):
                continue
            fname = re.sub(r"[^A-Za-z0-9_]", "_", i)        # remove non-alphanumeric characters from field names
            fname = re.sub(r"^([\d]+)", "_\1", fname)       # Neo4j field names cannot start with a number; prefix such fields with an underscore

            flds.append(fname + ":{" + fname + "}")
            data[fname] = data[i]                           # add "data" entry with neo4j-ready field name


        data['repository_id'] = int(repository_id)

        result = db.run("CREATE (n:Data" + typecode + " {" + ",".join(flds) + "}) RETURN ID(n) as i", data)
        id = None

        for record in result:
            id = record["i"]

        node_created = False
        summary = result.consume()
        if summary.counters.nodes_created >= 1:

            if id is not None:

                result = db.run("MATCH (r:Repository), (d:Data" + typecode + ") WHERE ID(d) = " + str(id) + " AND ID(r)= {repository_id} CREATE (r)<-[:PART_OF]-(d)", data)

                rel_created = False
                summary = result.consume()
                if summary.counters.relationships_created >= 1:
                    rel_created = True

                if rel_created:
                    ret['status_code'] = 200
                    ret['payload']['msg'] = "Added data " + typecode + "//" + str(repository_id)
                    ret['payload']['type'] = "xxx"
                else:
                    ret['status_code'] = 400
                    ret['payload']['msg'] = 'Something went wrong saving new data'

        return ret
