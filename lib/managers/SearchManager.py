from lib.utils.Db import db
import re
import json
from datetime import datetime
from lib.exceptions.SearchError import SearchError
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

class SearchManager:

    # For now all class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def quick(expression, nodeTypes=None, start=0, end=12, publishedOnly=False):
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
        elif isinstance(nodeTypes, basestring):
            nodeTypes = nodeTypes.split(",")
        ret = {'expression': expression, 'results': {}, 'counts': {}, 'total_counts': {}, 'slices': {}}
        for node in nodeTypes:
            res = SearchManager._execQuery(client, node, expression, start, end, publishedOnly)
            ret['results'][node] = res['results']
            ret['counts'][node] = res['count']
            ret['slices'][node] = res['slice']
            ret['total_counts'][node] = res['total_count']

        total_count = 0
        for node in ret['counts']:
            total_count += ret['counts'][node]
        ret['count'] = total_count

        return ret

    @staticmethod
    def portalSearch(expression, start=0, end=25):
        client = Elasticsearch()
        ret = {'nodes': [], 'Counts': {}}
        q = Q("bool", must=[Q('match', _all=expression)])
        s = Search(using=client, index="neo4j-inquisite-node", doc_type="Repository,Data").query(q)
        q_total = s.count()
        s = s[0:q_total]
        s = s.highlight_options(require_field_match=False)
        s = s.highlight('*', fragment_size=45)
        res = s.execute()
        data = {}
        uuids = []
        pub_uuids = {}
        if res:
            for r in res:
                d = r.to_dict()
                if r.meta.doc_type == 'Repository':
                    if int(d['published']) == 0:
                        continue
                    repo_id = r.meta.id
                    ret['nodes'].append({"id": r.meta.id, "type": "Repository", "name": d['name'], "description": d['readme']})
                    repo_uuids = SearchManager._getDataUUIDsForRepo(repo_id)
                    pub_uuids[repo_id] = repo_uuids
                else:
                    hits = []
                    highs = r.meta.highlight.to_dict()
                    for high_field,high_value in highs.items():
                        hits.append({high_field: high_value})
                    data[r.meta.id] = {'id': r.meta.id, "hits": hits}
                    uuids.append(r.meta.id)
            qString = "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE d.uuid IN {uuids} AND r.published = '1' RETURN d.uuid as uuid, r.name as repo_name, r.uuid as repo_id"
            pub_data = db.run(qString, {"uuids": uuids})
            data_max = 0
            for checked in pub_data:
                if data_max >= 32:
                    break;
                ret['nodes'].append({"id": checked['uuid'], "type": "Data", "repo_id": checked['repo_id'], "repo_name": checked['repo_name'], "hits": data[checked['uuid']]['hits']})
                data_max += 1

            return ret
        else:
            return ret

    @staticmethod
    def portalBrowse(type):
        ret = []
        if type == 'featured':
            match_string = "r.featured = {featured}"
            match_values = {"featured": "1"}
            qString = "MATCH (r:Repository) WHERE " + match_string + " RETURN r.uuid as repo_id, r.name as repo_name, r.readme as readme"
            repos = db.run(qString, match_values)
            for repo in repos:
                ret.append({
                    'type': 'Repository',
                    'id': repo['repo_id'],
                    'name': repo['repo_name'],
                    'description': repo['readme']
                })
        elif type == 'published':
            qString = "MATCH (r:Repository) WHERE r.published = {published} RETURN r.uuid as repo_id, r.name as repo_name, r.readme as readme, r.published_on as published_on"
            repos = db.run(qString, {"published": "1"})
            for repo in repos:
                ret.append({
                    'type': 'Repository',
                    'id': repo['repo_id'],
                    'name': repo['repo_name'],
                    'description': repo['readme'],
                    'published_on': repo['published_on']
                })
            print ret
            ret.sort(key=lambda x: datetime.strptime(x['published_on'], "%Y-%m-%d %H:%M:%S"), reverse=True)
            ret = ret[0:6]
        elif type == 'updated':
            qString = 'MATCH (r:Repository)<-[:IMPORTED_INTO]-(i:ImportEvent) WHERE r.published = {published} WITH r, max(i.started_on) as max RETURN max, r.uuid as repo_id, r.name as repo_name, r.readme as readme, r.published_on as published_on'
            repos = db.run(qString, {"published": "1"})
            for repo in repos:
                ret.append({
                    'type': 'Repository',
                    'id': repo['repo_id'],
                    'name': repo['repo_name'],
                    'description': repo['readme'],
                    'published_on': repo['published_on'],
                    'imported_on': repo['max']
                })
            ret.sort(key=lambda x: x['imported_on'], reverse=True)
            ret = ret[0:6]

        return {"nodes": ret}

    @staticmethod
    def _getDataUUIDsForRepo(repo_id):
        repo_uuids = []
        try:
            qString = "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE ID(r) = {repo_id} RETURN d.uuid as uuid"
            data = db.run(qString, {"repo_id": repo_id})
        except Exception as e:
            pass
        for d in data:
            repo_uuids.append(d.uuid)
        return repo_uuids

    @staticmethod
    def _execQuery(client, doc_type, expression, start, end, checkPub):
        try:
            s = Search(using=client, index="neo4j-inquisite-node", doc_type=doc_type) \
                .query("match", _all=expression)
        except Exception as e:
            raise SearchError(e.message)
        sub_ret = {"results": [], "count": 0, "slice": [(start+1), end]}
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
            repolist = {}
            schemaList = []
            uuids = []
            for i, r in enumerate(sub_ret['results']):
                uuids.append(r['__id'])
            # Populate repository and data type fields for data nodes
            if doc_type == 'Data':
                try:
                    if checkPub:
                        qString = "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE d.uuid IN {uuid} AND r.published = 1 RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, d.uuid as uuid, ID(t) as schema_id, t.name as schema_name"
                    else:
                        qString = "MATCH (r:Repository)--(t:SchemaType)--(d:Data) WHERE d.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, d.uuid as uuid, ID(t) as schema_id, t.name as schema_name"
                    nodes = db.run(qString, {"uuid": uuids})

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
                        rem = sub_ret['results'][i] = None
                        continue
                    sub_ret['count'] += 1
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
            elif doc_type == 'SchemaField' or doc_type == 'SchemaType':
                try:
                    if doc_type == 'SchemaField':
                        if checkPub:
                            qString = "MATCH (r:Repository)--(t:SchemaType)--(f:SchemaField) WHERE f.uuid IN {uuid} AND r.published = 1 RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, f.uuid as uuid, ID(t) as schema_id, t.name as schema_name"
                        else:
                            qString = "MATCH (r:Repository)--(t:SchemaType)--(f:SchemaField) WHERE f.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, f.uuid as uuid, ID(t) as schema_id, t.name as schema_name"
                        nodes = db.run(qString, {"uuid": uuids})
                    else:
                        if checkPub:
                            qString = "MATCH (r:Repository)--(t:SchemaType) WHERE t.uuid IN {uuid} AND r.published = 1 RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, t.uuid as uuid, ID(t) as schema_id, t.name as schema_name"
                        else:
                            qString = "MATCH (r:Repository)--(t:SchemaType) WHERE t.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid, t.uuid as uuid, ID(t) as schema_id, t.name as schema_name"
                        nodes = db.run(qString, {"uuid": uuids})
                    for n in nodes:
                        repolist[n['uuid']] = [n['repo_id'], n['repo_name'], n['repo_uuid'], n['schema_id'], n['schema_name']]
                        if n['schema_id'] not in schemaList:
                            schemaList.append(n['schema_id'])
                except Exception as e:
                    pass
                for i, r in enumerate(sub_ret['results']):
                    if r['__id'] not in repolist:
                        sub_ret['results'][i] = None
                        continue
                    sub_ret['count'] += 1
                    repoinfo = repolist[r['__id']]
                    sub_ret['results'][i]['__repo_id'] = repoinfo[0]
                    sub_ret['results'][i]['__repo_name'] = repoinfo[1]
                    sub_ret['results'][i]['__repo_uuid'] = repoinfo[2]
                    sub_ret['results'][i]['__schema_id'] = repoinfo[3]
                    sub_ret['results'][i]['__schema_name'] = repoinfo[4]
            elif doc_type == 'Repository':
                try:
                    if checkPub:
                        qString = "MATCH (r:Repository) WHERE r.uuid IN {uuid} AND r.published = 1 RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid"
                    else:
                        qString = "MATCH (r:Repository) WHERE r.uuid IN {uuid} RETURN ID(r) as repo_id, r.name as repo_name, r.uuid as repo_uuid"
                    nodes = db.run(qString, {"uuid": uuids})
                    for n in nodes:
                        repolist[n['repo_uuid']] = [n['repo_id'], n['repo_name'], n['repo_uuid']]
                except Exception as e:
                    pass
                for i, r in enumerate(sub_ret['results']):
                    if r['__id'] not in repolist:
                        sub_ret['results'][i] = None
                        continue
                    sub_ret['count'] += 1
                    repoinfo = repolist[r['__id']]
                    sub_ret['results'][i]['__repo_id'] = repoinfo[0]
                    sub_ret['results'][i]['__repo_name'] = repoinfo[1]
                    sub_ret['results'][i]['__repo_uuid'] = repoinfo[2]
            elif doc_type == 'Person':
                repos = {}
                try:
                    if checkPub:
                        qString = "MATCH (r:Repository)--(p:Person) WHERE p.uuid IN {uuid} AND r.published = 1 RETURN ID(p) as person_id, p.uuid as uuid, r.name as repo_name, ID(r) as repo_id, r.uuid as repo_uuid"
                    else:
                        qString = "MATCH (r:Repository)--(p:Person) WHERE p.uuid IN {uuid} RETURN ID(p) as person_id, p.uuid as uuid, r.name as repo_name, ID(r) as repo_id, r.uuid as repo_uuid"
                    nodes = db.run(qString, {"uuid": uuids})
                    for n in nodes:
                        if n['uuid'] in repos:
                            repos[n['uuid']].append([n['repo_name'], n['repo_id'], n['repo_uuid']])
                        else:
                            repos[n['uuid']] = [[n['repo_name'], n['repo_id'], n['repo_uuid']]]
                except Exception as e:
                    pass
                for i, r in enumerate(sub_ret['results']):
                    if r['__id'] not in repos:
                        sub_ret['results'][i] = None
                        continue
                    sub_ret['count'] += 1
                    sub_ret['results'][i].pop("password")
                    sub_ret['results'][i].pop("is_disabled")
                    sub_ret['results'][i].pop("is_admin")
                    sub_ret['results'][i].pop("created_on")
                    sub_ret['results'][i].pop("nyunetid")
                    sub_ret['results'][i].pop("prefs")
                    sub_ret['results'][i]['__repos'] = []
                    for repo in repos[r['__id']]:
                        sub_ret['results'][i]['__repos'].append(repo[0])
            if sub_ret['count'] < (end-start):
                sub_ret['slice'][1] = start+sub_ret['count']
        return sub_ret
