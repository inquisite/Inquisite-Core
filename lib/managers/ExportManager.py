from lib.utils.Db import db
import re
import datetime

class ExportManager:

    # For now all class methods are going to be static
    def __init__():
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def export(export_type, export_source):
        export = {
            "name": "export_placeholder",
            "time": str(datetime.datetime.now()),
            "exporter": "me [for now]",
            "uuid": '0000-000000-00000-000000-000000',
            "repos": []
        }
        if export_type == 'Repository':
            try:
                repo = db.run(
                    "MATCH (r:Repository) WHERE ID(r) = {id} RETURN ID(r) as repo_id, properties(r) as props", {"id": export_source}
                ).peek()
                print repo['repo_id'], repo['props']
            except Exception as e:
                print e.message
                pass
