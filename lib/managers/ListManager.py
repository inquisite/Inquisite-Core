from lib.utils.Db import db
import re
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.ValidationError import ValidationError
from lib.exceptions.SettingsValidationError import SettingsValidationError
from lib.decorators.Memoize import memoized

class ListManager:

    def __init__(self):
        pass

    @staticmethod()
    def addList(repo_id, name, code, description, items):

        check = {"exists": False}
        try:
            result = db.run("MATCH (l:List{code: {code}})--(r:Repository) WHERE ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description", {"code": code, "repo_id": repo_id})

            if result is not None and len(list(result)):
                ret = {"exists": True}
                for r in result:
                    ret["type"] = {
                        "id": r['id'],
                        "code": r['code'],
                        "name": r['name'],
                        'description': r['description']
                    }
                return ret
            else:
                result = db.run("MATCH (r:Repository) WHERE ID(r) = {repo_id} CREATE (l:List {name: {name}, code: {code}, description: {description}, storage: 'Graph'})-[:PART_OF]->(r) return ID(l) as id")
        except Exception as e:
            raise DbError(message="Could not add list: " + e.message, context="List.addList",
                          dberror=e.message)

        #add/edit List Items
        item_status = {}
        for item in items:
            item_res = ListManager.addListItem(repo_id, code, item['display'], item['code'], item['description'])

            if 'item_id' in item_res:
                item_status[item['code']] = {'status_code': 200, 'item_id': item_res['item_id'], 'msg': 'Created new list item'}
            else:
                item_status[item['code']] = {'status_code': 200, 'item_id': None, 'msg': 'Could not create list item'}

        if result:
            for r in result:
                ret['type'] = {
                    'id': r['id'],
                    'name': name,
                    'code': code,
                    'description': description,
                    'field_status': field_status
                }
                break
        else:
            raise DbError(message="Could not add list", context="List.addList",
                          dberror="")

        return ret

    @staticmethod
    def addListItem(repo_id, code, display, item_code, description):
        ret = {}
        if code is None or len(code) == 0:
            raise ValidationError(message="List code is required", context="List.addListItem")

        list_info = ListManager.getInfoForList(repo_id, code)
        if list_info is None:
            raise ValidationError(message="List code is invalid", context="List.addListItem")

        if display is None:
            raise ValidationError(message="Display value is required", context="List.addListItem")

        if item_code is None:
            raise ValidationError(message="List Item Code is required", context="List.addListItem")

        item_result = db.run("MATCH (i:ListItem {display: {display}})--(l:list {code: {code}})--(r:Repository) WHERE ID(r) = {repo_id} RETURN i.display as display, ID(i) as id", {"display": display, "code": code, "repo_id": repo_id}).peek()

        if item_result is not None:
            ret['exists'] = True
            ret['item_id'] = item_result['id']
            ret['display'] = item_result['display']
            return ret
        else:
            item_flds = ["display: {display}", "code: {item_code}", "description: {description}"]
            item_params = {"repo_id": repo_id, "display": display, "code": item_code, "description": description}

            add_result = db.run("MATCH (r:Repository)--(l:List {code: {code}}) WHERE ID(r) = {repo_id} CREATE (i:ListItem {" + ", ".join(item_flds) + "})-[:PART_OF]->(l) RETURN ID(i) as id, i.display as display, i.code as code", item_params)

            r = add_result.peek()

            if r:
                ret['exists'] = False
                ret['item_id'] = r['id']
                ret['display'] = r['display']
                ret['code'] = r['code']
                return ret
            else:
                raise DbError(message="Could not add List Item", context="List.addListItem", dberror="")



    @staticmethod
    def getInfoForList(repo_id, code):
        repo_id = int(repo_id)

        try:
            if isinstance(code, int):
                list_res = db.run("MATCH (r:Repository)--(l:List) WHERE ID(l) = {code} AND ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description as description", {"code" :code, "repo_id": repo_id}).peek()

                if list_res is None:
                    return None

                items_res = db.run("MATCH (i:ListItem)--(l:List)--(r:Repository) WHERE ID(l) = {code} AND ID(r) = {repo_id} RETURN ID(i) as id, i.display, display, i.code as code, i.description as description", {"code": code, "repo_id": repo_id})
            else:
                list_res = db.run("MATCH (r:Repository)--(l:List) WHERE l.code = {code} AND ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description as description", {"code" :code, "repo_id": repo_id}).peek()

                if list_res is None:
                    return None

                items_res = db.run("MATCH (i:ListItem)--(l:List)--(r:Repository) WHERE l.code = {code} AND ID(r) = {repo_id} RETURN ID(i) as id, i.display, display, i.code as code, i.description as description", {"code": code, "repo_id": repo_id})

            info = {'list_id': list_res['id'], 'name': list_res['name'], 'code': list_res['code'], 'description': list_res['description']}

            item_list = []
            if items_res:
                for r in items_res:
                    li = {'id': r['id'], 'display': r['display'], 'code': r['code'], 'description': r['description']}
                    item_list.append(li)

            info['fields'] = item_list
            return info

        except Exception as e:
            raise DbError(message="Could not get list items for list", context="List.getInfoForList", dberror=e.message)
