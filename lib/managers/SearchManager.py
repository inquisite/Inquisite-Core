from lib.utils.Db import db
import re
from lib.exceptions.SearchError import SearchError
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

class SearchManager:

    # For now all class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def quick(expression):
        client = Elasticsearch()

        try:
            s = Search(using=client, index="neo4j-inquisite-node") \
                .query("match", _all=expression)
        except Exception as e:
            raise SearchError(e.message)

        s = s[0:100]
        result = s.execute()
        #print "GOT"
        #print result

        ret = {'expression': expression, 'results': {}, 'counts': {}}

        if result:
            for r in result:
                d = r.to_dict()
                d['__id'] = r.meta.id
                d['__type'] = r.meta.doc_type
                d['__score'] = r.meta.score
                if r.meta.doc_type not in ret['results']:
                    ret['results'][r.meta.doc_type] = []
                    ret['counts'][r.meta.doc_type] = 0
                ret['results'][r.meta.doc_type].append(d)
                ret['counts'][r.meta.doc_type] = ret['counts'][r.meta.doc_type] + 1

            # Populate repository and data type fields for data nodes
            if 'Data' in ret['results']:
                uuids = []
                for i, r in enumerate(ret['results']['Data']):
                    uuids.append(r['__id'])

                repolist = {}
                try:
                    nodes = db.run(
                        "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE d.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, d.uuid as uuid",
                        {"uuid": uuids})

                    for n in nodes:
                        repolist[n['uuid']] = [n['repo_id'], n['repo_name'], n['repo_uuid']]
                except Exception as e:
                    pass

                for i, r in enumerate(ret['results']['Data']):
                    repoinfo = repolist[r['__id']]
                    ret['results']['Data'][i]['__repo_id'] = repoinfo[0]
                    ret['results']['Data'][i]['__repo_name'] = repoinfo[1]
                    ret['results']['Data'][i]['__repo_uuid'] = repoinfo[2]

            ret['count'] = len(result)
        else:
            ret['count'] = 0

        return ret