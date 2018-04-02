import re
from lib.utils.Db import db
from lib.utils.CypherHelpers import makeDataMapForCypher
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError
from lib.exceptions.LogError import LogError
from lib.exceptions.DbError import DbError
from lib.exceptions.FieldValidationError import FieldValidationError
from lib.exceptions.ParameterError import ParameterError
from lib.managers.SchemaManager import SchemaManager
from lib.managers.RepoManager import RepoManager
from timeit import default_timer as timer
import json
import time

class DataManager:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    # Returns id of newly created node
    #
    @staticmethod
    def add(repo_id, type_code, data, import_uuid=None):
        # TODO: does user have access to this repo?
        data_proc, type_info = DataManager._validateData(repo_id, type_code, data)
        try:
            q = "MATCH (t:SchemaType) WHERE ID(t) = {type_id} CREATE (n:Data " + makeDataMapForCypher(data_proc) + ")-[:IS]->(t) RETURN ID(n) AS id"

            data_proc["type_id"] = type_info["type_id"]     # add type_id to data before insert
            res = db.run(q, data_proc).peek()
            data_id = res["id"]

            if import_uuid is not None:
                db.run("MATCH (e:ImportEvent { uuid: {import_uuid}}), (n:Data) WHERE ID(n) = {data_id} CREATE (e)<-[x:IMPORTED_IN]-(n) RETURN ID(x) AS id", { "import_uuid": import_uuid, "data_id": data_id})


            #DataManager.logChange("I", data_proc)
            return data_id
        except Exception as e:
            raise DbError(message="Could not create data (" + e.__class__.__name__ + ") " + e.message, context="DataManager.add", dberror=e.message)

    #
    #
    #
    @staticmethod
    def _validateData(repo_id, type_code, data):
        type_info = SchemaManager.getInfoForType(repo_id, type_code)
        if type_info is None:
            raise FindError("Could not load type info")

        # gather data
        data_proc = {}
        row_errors = []
        for f in type_info["fields"]:
            v = None
            if f['code'] in data:
                v = data[f['code']]
            if v is None and f['id'] in data:
                v = data[f['id']]

            # Convert data-as-dict to JSON for serialized storage
            if isinstance(v, dict):
                v = json.dumps(v)

            if v is not None and isinstance(v, unicode) is False:
                if isinstance(v, basestring) is False:  # force non-string values to string prior to casting to unicode
                    v = str(v)
                v = unicode(v, errors='replace')
            if v is not None and v != '':
                dt = SchemaManager.getDataTypeInstanceForField(repo_id, type_code, f["code"], v)
                dtv = dt.validate(v)
                if dtv is not True:
                    row_errors.append(f['code'])
                    continue

                # Parse the data using the relevant datatype plugin
                # NOTE: If the datatype parser returns a dict we serialize to Neo4j with properties for each key
                # in the dict. This allows data types to serialize data across multiple node properties if required.
                # This is distinct from the case where the caller submits a dict as data. In that case we convert it to
                # JSON prior to performing any parsing.
                if f['type'] == 'ListDataType':
                    list_code = f['settings']['list_code']
                    parsed_value = dt.parse(v, list_code, repo_id)
                else:
                    parsed_value = dt.parse(v)

                # If a dict is returned we need to stored parsed value in multiple fields
                if isinstance(parsed_value, dict):
                    data_proc[f['code']] = v
                    for k, v in parsed_value.iteritems():
                        data_proc[f['code'] + "_" + k] = v
                else:
                    # simple scalar value is assigned direct
                    data_proc[f['code']] = parsed_value
                SchemaManager.getDataTypeInstanceForField.reset()
            else:
                data_proc[f['code']] = v
            if len(row_errors) > 0:
                raise FieldValidationError(message="Data is invalid for " + ", ".join(row_errors), errors=dtv,
                                           type=type_info['code'], field=f['code'], value=v,
                                           context="DataManager.add")
        return [data_proc, type_info]

    #
    #
    #
    @staticmethod
    def update(node_id, data, import_uuid=None):
        # TODO: does user have access to this repo?
        try:
            id = int(node_id)
        except:
            id = node_id

        try:
            if isinstance(id, (int)):
                res = db.run("MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE ID(d) = {node_id} RETURN ID(r) as repo_id, ID(t) as type_id", {"node_id": id}).peek()
            else:
                res = db.run(
                    "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE d.uuid = {uuid} RETURN ID(r) as repo_id, ID(t) as type_id",
                    {"uuid": id}).peek()
            if res is None:
                return None

            data_proc, type_info = DataManager._validateData(int(res['repo_id']), int(res['type_id']), data)

            if isinstance(id, (int)):
                data_proc["node_id"] = id
                db.run("MATCH (d:Data) WHERE ID(d) = {node_id} SET " + makeDataMapForCypher(data=data_proc, mode="U", prefix="d."), data_proc)
            else:
                data_proc["uuid"] = id
                db.run("MATCH (d:Data) WHERE d.uuid = {uuid} SET " + makeDataMapForCypher(data=data_proc, mode="U",
                                                                                            prefix="d."), data_proc)

            #DataManager.logChange("U", data_proc)
            return True
        except Exception as e:
            raise DbError(message="Could not update data", context="DataManager.update", dberror=e.message)

    #
    #
    #
    @staticmethod
    def delete(node_id, import_uuid=None):
        # TODO: does user have access to this repo?
        try:
            id = int(node_id)
        except:
            id = node_id

        try:
            if isinstance(id, (int)):
                db.run("MATCH (d:Data) WHERE ID(d) = {node_id} DELETE d", {"node_id": id})
            else:
                db.run("MATCH (d:Data) WHERE d.uuid = {uuid} DELETE d", {"uuid": id})

            # TODO: return false is no node is deleted?
            return True
        except Exception as e:
            raise DbError(message="Could not delete data", context="DataManager.delete", dberror=e.message)

    #
    # Delete data of specified types from repository. If type_code is a valid type or list of types
    # then only data of those type(s) will be removed. If type_codes is omitted all data regardless of type
    # will be removed.
    #
    @staticmethod
    def deleteDataFromRepo(repo_id, type_codes=None):
        # TODO: does user have access to this repo?

        type_str = ""
        if type_codes is not None:
            if all(isinstance(c, (int)) for c in type_codes):
                type_str = " AND ID(t) IN [" + ",".join(type_codes) + "] "
            else:
                type_codes = map(lambda x: '"' + re.sub(r'[^A-Za-z0-9_]+', '_', x) + '"', type_codes)
                type_str = " AND t.code IN [" + ",".join(type_codes) + "] "
        try:
            db.run("MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE ID(r) = {repo_id} " + type_str + " DETACH DELETE d", {"repo_id": repo_id})
            return True
        except Exception as e:
            raise DbError(message="Could not delete data from repository", context="DataManager.deleteDataFromRepo", dberror=e.message)

    #
    #
    #
    @staticmethod
    def addRelationship(start_node, end_node, type_id="RELATED", data=None):
        # TODO: does user have access to these nodes?
        try:
            type_id = re.sub(r'[^A-Za-z0-9_]+', '_', type_id)
            # NOTE: type_id is substituted directly into the string as the Bolt Neo4j driver doesn't allow placeholders for relationship types (yet)
            res = db.run("MATCH (d1:Data), (d2:Data) WHERE ID(d1) = {start_node} AND ID(d2) = {end_node} CREATE(d1)-[r:" + type_id + "]->(d2) RETURN ID(r) AS id", {"start_node": start_node, "end_node": end_node, "type_id": type_id}).peek()
            return res["id"]
        except Exception as e:
            raise DbError(message="Could not create relationship", context="DataManager.addRelationship", dberror=e.message)

    #
    # Synonym for DataManager.addRelationship()
    #
    @staticmethod
    def addRel(start_node, end_node, type_id=None, data=None):
        DataManager.addRelationship(start_node, end_node, type_id, data)

    #
    #
    #
    @staticmethod
    def editRelationship(rel_id, data):
        raise Exception("Not implemented yet")

    #
    # Synonym for DataManager.editRelationship()
    #
    @staticmethod
    def editRel(rel_id, data):
        DataManager.editRelationship(rel_id, data)

    #
    #
    #
    @staticmethod
    def deleteRelationship(start_node=None, end_node=None, type_id=None, rel_id=None):
        # TODO: does user have access to relationship?
        try:
            if type_id is not None:
                type_str = "r:" + re.sub(r'[^A-Za-z0-9_]+', '_', type_id)
            else:
                type_str = "r"

            # NOTE: type_id is substituted directly into the string as the Bolt Neo4j driver doesn't allow placeholders for relationship types (yet)

            if end_node is None:
                if rel_id is None:
                    rel_id = start_node     # if rel_id is not set assume first positional parameter (start_node) is the rel_id
                if rel_id is None:
                    return None

                # delete by rel_id
                db.run("MATCH (d1:Data)-[" + type_str + "]-(d2:Data) WHERE ID(r) = {rel_id} DELETE r", {"rel_id": rel_id})
            elif start_node is not None and end_node is not None:
                # delete by endpoints
                db.run("MATCH (d1:Data)-[" + type_str + "]-(d2:Data) WHERE ID(d1) = {start_node} AND ID(d2) = {end_node} DELETE r", {"start_node": start_node, "end_node": end_node})
            else:
                raise ParameterError(message="No relationship id or node id pair is set", context="DataManager.deleteRelationship")
            return True
        except Exception as e:
            raise DbError(message="Could not delete relationship", context="DataManager.deleteRelationship", dberror=e.message)

    #
    # Synonym for DataManager.deleteRelationship()
    #
    @staticmethod
    def deleteRel(start_node, end_node, type_id=None):
        DataManager.deleteRelationship(start_node, end_node, type_id)


    #
    # Load data node by ID
    #
    @staticmethod
    def getByID(node_id):
        # TODO: does user have access to this node?

        try:
            id = int(node_id)
            result = db.run(
                "MATCH (d:Data)--(t:SchemaType)--(r:Repository) WHERE ID(d) = {node_id} RETURN d, t.name as typename, t.code as typecode, ID(t) as schema_id, ID(r) as repo_id",
                {"node_id": id})
        except:
            result = db.run(
                "MATCH (d:Data)--(t:SchemaType)--(r:Repository) WHERE d.uuid = {uuid} RETURN d, ID(d) as node_id, t.name as typename, t.code as typecode, ID(t) as schema_id, ID(r) as repo_id",
                {"uuid": node_id})

        if result.peek():
            for r in result:
                    return {"node_id": r["node_id"], "typename": r["typename"], "typecode": r["typecode"], "schema_id": r["schema_id"], "repo_id": r["repo_id"], "data": r["d"].properties}
        else:
            raise FindError(message="Node does not exist")

    #
    # Get the total count of Data nodes for a Schema Type
    #
    @staticmethod
    def getCountForType(repo_id, type_id):
        repo_id = int(repo_id)
        type_id = int(type_id)
        try:
            q_count = db.run("MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE ID(r)={repo_id} AND ID(t)={type_id} RETURN count(d) as data_count", {"repo_id": repo_id, "type_id": type_id}).peek()

            return {"repo_id": repo_id, "type_id": type_id, "data_count": q_count['data_count']}
        except exception as e:
            raise DbError(message="Could get type Count", context="DataManager.getCountForType", dberror=e.message)

    @staticmethod
    def getDataForType(repo_id, type_code, start=0, limit=100):
        repo_id = int(repo_id)
        RepoManager.validate_repo_id(repo_id)
        type_info = SchemaManager.getInfoForType(repo_id, type_code)

        nodes = []
        cols = []
        c = 0

        try:
            # TODO: implement start/limit rather than fixed limit
            q = "MATCH (r:Repository)--(t:SchemaType)--(n:Data) WHERE ID(r)={repo_id} AND ID(t)={type_id} RETURN n SKIP {start} LIMIT {limit}"

            result = db.run(q, {"repo_id": repo_id, "type_id": type_info["type_id"],  "start": start, "limit": limit})
            if result is not None:
                for data in result:
                    nodes.append(data.items()[0][1].properties)
                    c = c + 1

                if len(nodes) > 0:
                    cols = nodes[0].keys()

            return {"data": nodes, "columns": cols, "type_id": type_info["type_id"], "repo_id": repo_id, "start": start, "limit": limit, "count": c}
        except Exception as e:
            return {"data": [], "columns": [], "type_id": type_info["type_id"], "repo_id": repo_id, "start": start,
                    "limit": limit, "count": 0}

    #
    # Versioning
    #
    @staticmethod
    def logChange(change_type, data, user_id=None):
        # TODO: does user have access to this node?
        data['_change_type'] = change_type
        data['_datetime'] = time.time()
        uuid = data['uuid']
        del(data['uuid'])
        try:
            q = "MATCH (d:Data) WHERE d.uuid = {uuid} CREATE (v:DataLog " + makeDataMapForCypher(
                data) + ")-[:LOG]->(d) RETURN ID(v) AS id"
            data['uuid'] = uuid
            data['user_id'] = user_id
            result = db.run(q, data)
            if result is not None:
                for data in result:
                    return {"log_id": data['id']}
            raise LogError(message="Failed to return log_id")
        except Exception as e:
            raise LogError(message="Failed to create log entry")

    @staticmethod
    def getChangeLog():
        pass
