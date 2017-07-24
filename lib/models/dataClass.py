import re
from lib.utils.db import db
from lib.utils.cypherHelpers import makeDataMapForCypher
from lib.exceptions.SaveError import SaveError
from lib.exceptions.FindError import FindError

class Data:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    @staticmethod
    def getNode(node_id):

        result = db.run(
            "MATCH (d:Data)--(t:SchemaType) WHERE ID(d) = {node_id} RETURN d, t.name as typename, t.code as typecode",
            {"node_id": int(node_id)})

        if result.peek():
            for r in result:
                return {"node_id": node_id, "typename": r["typename"], "typecode": r["typecode"], "data": r["d"].properties}
        else:
            raise FindError(message="Node does not exist")

        return ret

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