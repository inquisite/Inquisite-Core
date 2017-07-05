from inquisite.db import db
import re
from lib.utils import makeDataMapForCypher

class Data:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    @staticmethod
    def getNode(node_id):
        # TODO: check that user has access to this data

        result = db.run(
            "MATCH (d:Data)--(t:SchemaType) WHERE ID(d) = {node_id} RETURN d, t.name as typename, t.code as typecode",
            {"node_id": int(node_id)})

        ret = {'status_code': 200, 'payload': {}}

        # TODO: clean up payload
        if result.peek():
            for r in result:
                ret['status_code'] = 200
                ret['payload']['node_id'] = node_id
                ret['payload']['typename'] = r['typename']
                ret['payload']['typecode'] = r['typecode']
                ret['payload']['data'] = r['d'].properties
                break
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Could not find data'

        return ret

    @staticmethod
    def saveNode(node_id, data):
        # TODO: check that user has access to this data

        f = data.copy()
        f['node_id'] = int(node_id);
        result = db.run(
            "MATCH (d:Data) WHERE ID(d) = {node_id} SET d = " + makeDataMapForCypher(data) + " RETURN count(d) as c",
            f)

        ret = {'status_code': 200, 'payload': {}}

        # TODO: clean up payload
        if result.peek():
            for r in result:
                ret['status_code'] = 200
                ret['payload']['node_id'] = node_id
                ret['payload']['count'] = r['c']
                break
        else:
            ret['status_code'] = 400
            ret['payload']['msg'] = 'Could not update data'

        return ret
