from lib.utils.Db import db
import re
import datetime
import json
from RepoManager import RepoManager
from SchemaManager import SchemaManager
from DataManager import DataManager

class ExportManager:

    # For now all class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def export(export_type, repo_id, schema_id):
        export = {
            "name": "export_placeholder",
            "time": str(datetime.datetime.now()),
            "exporter": "me [for now]",
            "uuid": '0000-000000-00000-000000-000000',
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
                    schema_data = DataManager.getDataForType(repo_id, schema_info[i]['id'])
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

                # Get data for this schema
                schema_data = DataManager.getDataForType(repo_id, schema_id)

                repo_info['schemas'] = schema_info

                export['repos'].append(repo_info)
            except Exception as e:
                print e.message
                pass
        else:
            pass


        return export
