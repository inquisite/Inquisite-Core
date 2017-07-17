from lib.utils.db import db
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
    def addType(repository_id, name, code, description, fields):

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


            # add fields
            # add/edit fields
            field_status = {}
            for k in fields:
                # add field
                fret = Schema.addField(repository_id, code, k['name'], k['code'], k['type'],
                                           k['description'])

                if 'field_id' in fret['payload']:
                    field_status[k['code']] = {'status_code': 200, 'field_id': fret['payload']['field_id'],
                                                           'msg': 'Created new field'}
                else:
                    field_status[k['code']] = {'status_code': 200, 'field_id': None,
                                                           'msg': 'Could not create new field'}

            # TODO: clean up payload
            if result:
                for r in result:
                    ret['status_code'] = 200
                    ret['payload']['msg'] = "Added type " + name + "//" + str(repository_id)
                    ret['payload']['type'] = {
                        "id": r['id'],
                        "name": name,
                        "code": code,
                        "description": description,
                        "field_status": field_status
                    }
                    break
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong saving new type'


        return ret

    @staticmethod
    def editType(repository_id, type_id, name, code, description, fields, fieldsToDelete):

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

        # add/edit fields
        field_status = {}
        for k in fields:
            if 'id' in fields[k]:
                # edit existing field
                fret = Schema.editField(repository_id, code, fields[k]['id'], fields[k]['name'], fields[k]['code'], fields[k]['type'],
                                       fields[k]['description'])

                if 'field_id' in fret['payload']:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': fret['payload']['field_id'],
                                                       'msg': 'Edited field'}
                else:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': None,
                                                       'msg': 'Could not edit field'}
            else:
                # add field
                fret = Schema.addField(repository_id, code, fields[k]['name'], fields[k]['code'], fields[k]['type'], fields[k]['description'])

                if 'field_id' in fret['payload']:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': fret['payload']['field_id'], 'msg': 'Created new field'}
                else:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': None, 'msg': 'Could not create new field'}

        # delete fields
        if fieldsToDelete:
            for field_id in fieldsToDelete:
                Schema.deleteField(repository_id, code, field_id)


        # TODO: clean up payload
        if result:
            for r in result:
                ret['status_code'] = 200
                ret['payload']['msg'] = "Edited type " + name
                ret['payload']['type'] = {
                    "id": r['id'],
                    "name": name,
                    "code": code,
                    "description": description,
                    "field_status": field_status
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

        try:
            result = db.run("MATCH (t:SchemaType)-[x]-(r:Repository) WHERE ID(r) = {repository_id} AND ID(t) = {type_id} optional match (f:SchemaField)-[y]-(t) DELETE x,y,t,f",
                            {"type_id": int(type_id), "repository_id": int(repository_id)})
            #r = result.peek()
            if result is not None:
                ret['status_code'] = 200
                ret['payload']['msg'] = "Deleted type " + str(type_id)
                ret['payload']['repository_id'] =  repository_id
                ret['payload']['type_id'] = type_id
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong deleting type'
        except:
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
        if result is not None:
            ret['payload']['msg'] = "Field already exists"
        else:
            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}}) WHERE ID(r) = {repository_id} CREATE (f:SchemaField { name: {name}, code: {code}, description: {description}, type: {fieldtype} })-[:PART_OF]->(t) RETURN ID(f) as id",
                {"repository_id": int(repository_id), "name": name, "code": code, "description": description,
                 "typecode": typecode, "fieldtype": fieldtype})
            r = result.peek()

            # TODO: check query result

            # TODO: clean up payload
            if r:
                ret['payload']['xxx'] = 'xxx'
                ret['status_code'] = 200
                ret['payload']['msg'] = "Added field " + name + "//" + str(repository_id)
                ret['payload']['field_id'] = r['id']
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong saving new field'

        return ret

    @staticmethod
    def editField(repository_id, typecode, field_id, name, code, fieldtype, description):
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
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repository_id} AND ID(f) <> {field_id}  RETURN t",
            {"typecode": typecode, "code": code, "repository_id": int(repository_id), "field_id": int(field_id)}).peek()
        if result is not None:
            ret['status_code'] = 400
            ret['payload']['msg'] = "Field already exists"
        else:
            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}})--(f:SchemaField) WHERE ID(r) = {repository_id} AND ID(f) = {field_id} SET f.name = {name}, f.code = {code}, f.description = {description}, f.type = {fieldtype} RETURN ID(f) as id",
                {"repository_id": int(repository_id), "name": name, "code": code, "description": description,
                 "typecode": typecode, "fieldtype": fieldtype, "field_id": int(field_id)})
            r = result.peek()

            # TODO: check query result

            # TODO: clean up payload
            if r:
                ret['payload']['xxx'] = 'xxx'
                ret['status_code'] = 200
                ret['payload']['msg'] = "Edited field " + field_id + "//" + str(repository_id)
                ret['payload']['field_id'] = r['id']
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong when editing field'
        return ret

    @staticmethod
    def deleteField(repository_id, typecode, field_id):
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
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}})-[x]-(f:SchemaField) WHERE ID(r) = {repository_id} AND ID(f) = {field_id} DELETE f,x",
                {"repository_id": int(repository_id),  "field_id": int(field_id), "typecode": typecode})

            if result is not None:
                ret['status_code'] = 200
                ret['payload']['msg'] = "Deleted field "
                ret['payload']['repository_id'] =  repository_id
            else:
                ret['status_code'] = 400
                ret['payload']['msg'] = 'Something went wrong deleting field'
        except:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Something went wrong deleting field'

        return ret

    @staticmethod
    def createDataTypeFromFields(repository_id, typecode, field_names):
        typecode_proc = re.sub(r"[^A-Za-z0-9_]", "_", typecode)[0:15].strip()
        typecode_proc_disp = re.sub(r"[_]", " ", typecode_proc).strip()
        field_spec = []
        for f in field_names:
            fproc = re.sub(r'[^A-Za-z0-9_]+', '_', f).lower()
            fproc_disp = re.sub(r'[_]+', ' ', fproc).title()
            field_spec.append({
                'name': fproc_disp,
                'code': fproc,
                'description': 'Created by data import',
                'type': 'TEXT'  # TODO: support other types
            })

        Schema.addType(repository_id, typecode_proc_disp, typecode_proc, "Created by data import", field_spec)

        return field_names
    @staticmethod
    def addDataToRepo(repository_id, typecode, data):
        ret = {
            'status_code': 200,
            'payload': {
                'msg': 'Success',
                'type': ''
            }
        }

        typecode_proc = re.sub(r"[^A-Za-z0-9_]", "_", typecode)[0:15].strip()

        # TODO: check that repository is owned by current user

        # TODO: verify fields present are valid for this type
        # TODO: validate each field value

        flds = []
        for i in data.keys():
            if (i == '_ID'):
                continue
            fname = re.sub(r"[^A-Za-z0-9_]", "_", i)        # remove non-alphanumeric characters from field names
            fname = re.sub(r"^([\d]+)", "_\1", fname).strip()      # Neo4j field names cannot start with a number; prefix such fields with an underscore


            flds.append(fname + ":{" + fname + "}")
            data[fname] = data[i]                           # add "data" entry with neo4j-ready field name


        data['repository_id'] = int(repository_id)
        data['typecode_proc'] = typecode_proc

        q = "MATCH (t:SchemaType{code: {typecode_proc}}) CREATE (n:Data {" + ",".join(flds) + "})-[:IS]->(t) RETURN ID(n) as id"

        result = db.run(q, data)
        id = None

        for record in result:
            id = record['id']

        node_created = False
        summary = result.consume()
        if summary.counters.nodes_created >= 1:

            if id is not None:

                #result = utils.run("MATCH (r:Repository), (d:Data) WHERE ID(d) = " + str(id) + " AND ID(r)= {repository_id} CREATE (r)<-[:PART_OF]-(d)", data)

                rel_created = False
                #summary = result.consume()
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
