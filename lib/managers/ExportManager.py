from lib.utils.Db import db
import re
import datetime
import json
from uuid import uuid4
from RepoManager import RepoManager
from SchemaManager import SchemaManager
from DataManager import DataManager

class ExportManager:

    # For now all class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def export(export_name, export_user, export_type, repo_id=None, schema_id=None, record_ids=None):
        export_name = export_name + '_' + export_type + '_export'
        export = {
            "name": export_name,
            "time": str(datetime.datetime.now()),
            "exporter": export_user,
            "uuid": uuid4().hex,
            "repos": []
        }
        if export_type == 'Repository':
            try:
                # Get core info about repository
                repo_info = RepoManager.getInfo(repo_id)

                # Get all field information for all schemas for this repo
                schema_info = SchemaManager.getTypes(repo_id)

                # Get all data for each schema in this repo
                for i in range(len(schema_info)):

                    data_count = DataManager.getCountForType(repo_id, schema_info[i]['id'])
                    data_total = data_count['data_count']

                    schema_data = DataManager.getDataForType(repo_id, schema_info[i]['id'], 0, data_total)
                    #print schema_data
                    schema_info[i]['data'] = schema_data

                repo_info['schemas'] = schema_info

                export['repos'].append(repo_info)

            except Exception as e:
                print e.message
                pass
        elif export_type == 'Schema':
            try:
                # Get core info about repository
                repo_info = RepoManager.getInfo(repo_id)

                # Get all field information for all schemas for this repo
                schema_info = SchemaManager.getType(repo_id, schema_id)

                # Get the total count of records for this type

                data_count = DataManager.getCountForType(repo_id, schema_id)
                data_total = data_count['data_count']
                print repo_id, schema_id, data_total
                # Get data for this schema
                schema_data = DataManager.getDataForType(repo_id, schema_id, 0, data_total)
                schema_info['data'] = schema_data
                repo_info['schemas'] = schema_info

                export['repos'].append(repo_info)
            except Exception as e:
                print e.message
                pass
        else:
            try:
                raw_results = {}
                for node_id in record_ids:
                    print node_id
                    node_data = DataManager.getByID(node_id)

                    if node_data:
                        if node_data['repo_id'] not in raw_results:
                            raw_results[node_data['repo_id']] = {}
                        if node_data['schema_id'] not in raw_results[node_data['repo_id']]:
                            raw_results[node_data['repo_id']][node_data['schema_id']] = []
                        raw_results[node_data['repo_id']][node_data['schema_id']].append(node_data['data'])
                print raw_results
                for repo_id in raw_results:
                    repo_info = RepoManager.getInfo(repo_id)
                    repo_info['schemas'] = []
                    for schema_id in raw_results[repo_id]:
                        schema_info = SchemaManager.getType(repo_id, schema_id)
                        schema_info['data'] = raw_results[repo_id][schema_id]
                        repo_info['schemas'].append(schema_info)

                    export['repos'].append(repo_info)

            except Exception as e:
                print e.message
                pass




        return export
