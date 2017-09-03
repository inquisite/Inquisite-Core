import re
from lib.utils.Db import db
from lib.utils.CypherHelpers import makeDataMapForCypher
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError

class DataManager:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    #
    #
    @staticmethod
    def add(repo_id, ):
        pass


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