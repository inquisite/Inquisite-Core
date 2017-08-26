from lib.utils.db import db
import re
from lib.exceptions.SearchError import SearchError

class SearchManager:

    # For now all class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def quick(expression):
        result = db.run(
            "MATCH (n:Data)--(t:SchemaType)--(r:Repository) WHERE any(prop in keys(n) where TOSTRING(n[prop]) CONTAINS {expression}) return ID(r) as repository_id, r.name as repository_name, t.name as typename, ID(n) as data_id, n limit 50",
            {"expression": expression})

        ret = {'expression': expression, 'results': []}

        if result:
            display_prop = None
            max_len = 0
            for r in result:
                if display_prop is None:
                    for property, value in (r['n'].properties).iteritems():
                        if isinstance(value, str):
                            l = len(value.encode('utf-8').strip())
                        else:
                            l = len(str(value))

                        if l > max_len:
                            max_len = l
                            display_prop = property

                ret['results'].append({
                    'repository_id': r['repository_id'],
                    'repository_name': r['repository_name'],
                    'data_id': r['data_id'],
                    #'p': display_prop,
                    #'l': max_len,
                    'display': r['n'][display_prop][0:100]
                })
            ret['count'] = len(ret['results'])
            return ret

        raise SearchError("Could not execute search")