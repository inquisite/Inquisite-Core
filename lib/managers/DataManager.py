import re
from lib.utils.Db import db
from lib.utils.CypherHelpers import makeDataMapForCypher
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.FieldValidationError import FieldValidationError
from lib.exceptions.ParameterError import ParameterError
from lib.managers.SchemaManager import SchemaManager

class DataManager:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    # Returns id of newly created node
    #
    @staticmethod
    def add(repo_id, type_code, data):
        # TODO: does user have access to this repo?

        data_proc, type_info = DataManager._validateData(repo_id, type_code, data)

        try:
            q = "MATCH (t:SchemaType) WHERE ID(t) = {type_id} CREATE (n:Data " + makeDataMapForCypher(data_proc) + ")-[:IS]->(t) RETURN ID(n) as id"

            data_proc["type_id"] = type_info["type_id"]     # add type_id to data before insert

            res = db.run(q, data_proc).peek()

            return res["id"]
        except Exception as e:
            print e.message
            raise DbError(message="Could not create data", context="DataManager.add", dberror=e.message)

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
        for f in type_info["fields"]:
            if f['code'] in data:
                v = data[f['code']]
                dt = SchemaManager.getDataTypeInstanceForField(repo_id, type_code, f["code"], data[f['code']])
                dtv = dt.validate(v)

                if dtv is not True:
                    raise FieldValidationError(message="Data is invalid for " + f['code'], errors=dtv,
                                               type=type_info['code'], field=f['code'], value=v,
                                               context="DataManager.add")

                # TODO: perform transformation here

                data_proc[f['code']] = v
        return [data_proc, type_info]

    #
    #
    #
    @staticmethod
    def update(node_id, data):
        # TODO: does user have access to this repo?

        try:
            res = db.run("MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE ID(d) = {node_id} RETURN ID(r) as repo_id, ID(t) as type_id", {"node_id": node_id}).peek()
            if res is None:
                return None
            data_proc, type_info = DataManager._validateData(int(res['repo_id']), int(res['type_id']), data)

            data_proc["node_id"] = node_id
            db.run("MATCH (d:Data) WHERE ID(d) = {node_id} SET " + makeDataMapForCypher(data=data_proc, mode="U", prefix="d."), data_proc)

            return True
        except Exception as e:
            print e.message
            raise DbError(message="Could not update data", context="DataManager.update", dberror=e.message)

    #
    #
    #
    @staticmethod
    def delete(node_id):
        # TODO: does user have access to this repo?
        try:
            db.run("MATCH (d:Data) WHERE ID(d) = {node_id} DELETE d")

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
                type_codes = map(lambda x: '"' + re.sub(r'[^A-Za-z0-9_\-]+', '_', x) + '"', type_codes)
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
            type_id = re.sub(r'[^A-Za-z0-9_\-]+', '_', type_id)
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
                type_str = "r:" + re.sub(r'[^A-Za-z0-9_\-]+', '_', type_id)
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


    # ------------------------------------------------------------
    # OLD METHODS
    # ------------------------------------------------------------
    #
    # Load data node by ID
    #
    @staticmethod
    def getNodeByID(node_id):

        result = db.run(
            "MATCH (d:Data)--(t:SchemaType) WHERE ID(d) = {node_id} RETURN d, t.name as typename, t.code as typecode",
            {"node_id": int(node_id)})

        if result.peek():
            for r in result:
                return {"node_id": node_id, "typename": r["typename"], "typecode": r["typecode"], "data": r["d"].properties}
        else:
            raise FindError(message="Node does not exist")

        return ret

    #
    # Edit node using provided data
    # TODO: remove?
    #
    @staticmethod
    def saveNode(node_id, data):
        # TODO: check that user has access to this data

        f = data.copy()
        f['node_id'] = int(node_id);
        result = db.run(
            "MATCH (d:Data) WHERE ID(d) = {node_id} SET d = " + makeDataMapForCypher(data) + " RETURN count(d) as c",
            f)

        if result.peek():
            for r in result:
                return {"node_id": node_id, "count": r["c"] }
        else:
            raise SaveError(message="Could not save node")


    #
    # TODO: remove?
    #
    @staticmethod
    def createDataTypeFromFields(repo_id, typecode, field_names):
        typecode_proc = re.sub(r"[^A-Za-z0-9_]", "_", typecode)[0:15].strip()
        typecode_proc_disp = re.sub(r"[_]", " ", typecode_proc).strip()
        field_spec = {}
        for f in field_names:
            fproc = re.sub(r'[^A-Za-z0-9_]+', '_', f).lower()
            fproc_disp = re.sub(r'[_]+', ' ', fproc).title()
            field_spec[fproc] = {
                'name': fproc_disp,
                'code': fproc,
                'description': 'Created by data import',
                'type': 'TextDataType'  # TODO: support other types
            }

        SchemaManager.addType(repo_id, typecode_proc_disp, typecode_proc, "Created by data import", field_spec)

        return field_names

    #
    # Todo: remove?
    #
    @staticmethod
    def addDataToRepo(repo_id, typecode, data):

        typecode_proc = re.sub(r"[^A-Za-z0-9_]", "_", typecode)[0:15].strip()

        # TODO: check that repository is owned by current user

        # TODO: verify fields present are valid for this type
        # TODO: validate each field value

        flds = []
        for i in data.keys():
            if (i == '_ID'):
                continue
            fname = re.sub(r"[^A-Za-z0-9_]", "_", i)  # remove non-alphanumeric characters from field names
            fname = re.sub(r"^([\d]+)", "_\1",
                           fname).strip()  # Neo4j field names cannot start with a number; prefix such fields with an underscore

            flds.append(fname + ":{" + fname + "}")
            data[fname] = data[i]  # add "data" entry with neo4j-ready field name

        data['repo_id'] = int(repo_id)
        data['typecode_proc'] = typecode_proc

        q = "MATCH (t:SchemaType{code: {typecode_proc}}) CREATE (n:Data {" + ",".join(
            flds) + "})-[:IS]->(t) RETURN ID(n) as id"

        try:
            result = db.run(q, data)
        except Exception as e:
            raise DbError(message="Could not create data", context="Schema.addDataToRepo", dberror=e.message)
        id = None

        for record in result:
            id = record['id']

        node_created = False
        summary = result.consume()
        if summary.counters.nodes_created >= 1:

            if id is not None:

                # result = utils.run("MATCH (r:Repository), (d:Data) WHERE ID(d) = " + str(id) + " AND ID(r)= {repo_id} CREATE (r)<-[:PART_OF]-(d)", data)

                rel_created = False
                # summary = result.consume()
                if summary.counters.relationships_created >= 1:
                    rel_created = True

                if rel_created:
                    return True
                else:
                    return False