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
    def quick(expression, nodeTypes=None, start=0, end=100):
        client = Elasticsearch()
        if not nodeTypes:
            nodeTypes = [
                "Repository",
                "Data",
                "SchemaType",
                "SchemaField",
                "List"
                "ListItem",
                "Person",
            ]
        ret = {'expression': expression, 'results': {}, 'counts': {}, 'total_counts': {}}
        for node in nodeTypes:
            res = SearchManager._execQuery(client, node, expression, start, end)
            ret['results'][node] = res['results']
            ret['counts'][node] = res['count']
            ret['total_counts'][node] = res['total_count']

        total_count = 0
        for node in ret['counts']:
            total_count += ret['counts'][node]
        ret['count'] = total_count

        return ret

    @staticmethod
    def _execQuery(client, doc_type, expression, start, end):
        try:
            s = Search(using=client, index="neo4j-inquisite-node", doc_type=doc_type) \
                .query("match", _all=expression)
        except Exception as e:
            raise SearchError(e.message)
        sub_ret = {"results": [], "count": 0}
        s = s[start:end]
        result = s.execute()
        sub_ret['total_count'] = result.hits.total
        if result:
            for r in result:
                d = r.to_dict()
                d['__id'] = r.meta.id
                d['__type'] = r.meta.doc_type
                d['__score'] = r.meta.score
                sub_ret['results'].append(d)
                sub_ret['count'] += 1

            repolist = {}
            schemaList = []
            uuids = []
            for i, r in enumerate(sub_ret['results']):
                uuids.append(r['__id'])
            # Populate repository and data type fields for data nodes
            if doc_type == 'Data':
                try:
                    nodes = db.run(
                        "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE d.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, d.uuid as uuid, ID(t) as schema_id, t.name as schema_name",
                        {"uuid": uuids})

                    for n in nodes:
                        repolist[n['uuid']] = [n['repo_id'], n['repo_name'], n['repo_uuid'], n['schema_id'], n['schema_name']]
                        if n['schema_id'] not in schemaList:
                            schemaList.append(n['schema_id'])
                    schemaFields = {}
                    schemas = db.run("MATCH (t:SchemaType)--(f:SchemaField) WHERE ID(t) in {schema} RETURN ID(f) as field_id, f.code as code, f.settings_search_display as search_display, ID(t) as schema_id ", {"schema": schemaList})
                    for schemaField in schemas:
                        if schemaField['schema_id'] not in schemaFields:
                            schemaFields[schemaField['schema_id']] = []
                        schemaFields[schemaField['schema_id']].append([schemaField['field_id'], schemaField['code'], schemaField['search_display']])
                except Exception as e:
                    pass
                for i, r in enumerate(sub_ret['results']):
                    if r['__id'] not in repolist:
                        continue
                    repoinfo = repolist[r['__id']]
                    sub_ret['results'][i]['__repo_id'] = repoinfo[0]
                    sub_ret['results'][i]['__repo_name'] = repoinfo[1]
                    sub_ret['results'][i]['__repo_uuid'] = repoinfo[2]
                    sub_ret['results'][i]['__schema_id'] = repoinfo[3]
                    sub_ret['results'][i]['__schema_name'] = repoinfo[4]
                    schemaInfo = schemaFields[repoinfo[3]]
                    for field in schemaInfo:
                        if field[2] == 'false' or field[2] == '0':
                            sub_ret['results'][i].pop(field[1], None)
            elif doc_type == 'SchemaField':
                try:
                    nodes = db.run(
                        "MATCH (r:Repository)--(t:SchemaType)--(f:SchemaField) WHERE f.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, f.uuid as uuid, ID(t) as schema_id, t.name as schema_name",
                        {"uuid": uuids})
                    for n in nodes:
                        repolist[n['uuid']] = [n['repo_id'], n['repo_name'], n['repo_uuid'], n['schema_id'], n['schema_name']]
                        if n['schema_id'] not in schemaList:
                            schemaList.append(n['schema_id'])
                except Exception as e:
                    print e.message
                    pass
                print repolist
                for i, r in enumerate(sub_ret['results']):
                    if r['__id'] not in repolist:
                        continue
                    repoinfo = repolist[r['__id']]
                    sub_ret['results'][i]['__repo_id'] = repoinfo[0]
                    sub_ret['results'][i]['__repo_name'] = repoinfo[1]
                    sub_ret['results'][i]['__repo_uuid'] = repoinfo[2]
                    sub_ret['results'][i]['__schema_id'] = repoinfo[3]
                    sub_ret['results'][i]['__schema_name'] = repoinfo[4]

        return sub_ret
