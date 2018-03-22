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

    @staticmethod
    def addList(repo_id, name, code, description='', items={}):
        try:
            repo_id = int(repo_id)
        except TypeError:
            raise DbError(message="Invalid repo_id provided", context="List.addList",
                          dberror="")
        ret = {"exists": False}
        try:
            result = db.run("MATCH (l:List{code: {code}})--(r:Repository) WHERE ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description as description", {"code": code, "repo_id": int(repo_id)})

            if result.peek() is not None and len(list(result)):
                ret["exists"] = True
                print result.peek(), list(result)
                for r in result:
                    print r
                    ret["type"] = {
                        "id": r['id'],
                        "code": r['code'],
                        "name": r['name'],
                        'description': r['description']
                    }
                    break
                print "Returing existing List"
                return ret
            else:
                result = db.run("MATCH (r:Repository) WHERE ID(r) = {repo_id} CREATE (l:List {name: {name}, code: {code}, description: {description}, storage: 'Graph'})-[:PART_OF]->(r) return ID(l) as id", {"repo_id": repo_id, "name": name, "code": code, "description": description})
        except Exception as e:
            print e.message
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
                ret["type"] = {
                    'id': r['id'],
                    'name': name,
                    'code': code,
                    'description': description,
                    'list_status': item_status
                }
                break
        else:
            raise DbError(message="Could not add list", context="List.addList",
                          dberror="")

        return ret

    @staticmethod
    def editList(repo_id, list_id, name, code, description, items, delete_items):
        try:
            repo_id = int(repo_id)
            list_id = int(list_id)
        except TypeError:
            raise DbError(message="Invalid repo_id or list_id provided", context="List.addListItem",
                          dberror="")
        result = db.run(
            "MATCH (r:Repository)--(l:List) WHERE ID(r) = {repo_id} AND ID(l) = {list_id} SET l.name = {name}, l.code = {code}, l.description = {description} RETURN ID(l) AS id",
            {"repo_id": int(repo_id), "list_id": int(list_id), "name": name, "code": code, "description": description})

        # add/edit fields
        item_status = {}
        print items
        for k in items:
            print items[k]
            if 'id' in items[k]:
                # edit existing field
                li_ret = ListManager.editListItem(repo_id, code, items[k].get('id', ''), items[k].get('display', ''), items[k].get('code', ''), items[k]['description'])

                if 'item_id' in li_ret:
                    item_status[items[k]['code']] = {'status_code': 200, 'item_id': li_ret['item_id'],
                                                       'msg': 'Edited list item'}
                else:
                    item_status[items[k]['code']] = {'status_code': 200, 'item_id': None,
                                                       'msg': 'Could not edit list item'}
            else:
                # add field
                li_ret = ListManager.addListItem(repo_id, code, items[k].get('display', ''), items[k].get('code', ''), items[k].get('description', ''))

                if 'item_id' in li_ret:
                    item_status[items[k]['code']] = {'status_code': 200, 'item_id': li_ret['item_id'], 'msg': 'Created new list item'}
                else:
                    item_status[items[k]['code']] = {'status_code': 200, 'item_id': None, 'msg': 'Could not create new list item'}

        # delete fields
        if delete_items:
            for item_id in delete_items:
                ListManager.deleteListItem(repo_id, code, item_id)


        if result:
            ret = {}
            for r in result:
                ret['type'] = {
                    "id": r['id'],
                    "name": name,
                    "code": code,
                    "description": description,
                    "item_status": item_status
                }
                return ret
        else:
            raise DbError(message="Could not edit list", context="List.editList",
                          dberror="")

    @staticmethod
    def deleteList(repo_id, list_id):
        try:
            result = db.run("MATCH (l:List)-[x]-(r:Repository) WHERE ID(r) = {repo_id} AND ID(l) = {list_id} OPTIONAL MATCH (i:ListItem)-[y]-(l) DELETE x,y,l,i",
                            {"list_id": int(list_id), "repo_id": int(repo_id)})

            if result is not None:
                return {"list_id": list_id}
            else:
                raise FindError(message="Could not find list", context="Schema.deleteList", dberror="")
        except Exception as e:
            raise DbError(message="Could not delete list", context="Schema.deleteList", dberror=e.message)

    @staticmethod
    def addListItem(repo_id, code, display, item_code, description=None):
        try:
            repo_id = int(repo_id)
        except TypeError:
            raise DbError(message="Invalid repo_id provided", context="List.addListItem",
                          dberror="")
        ret = {}
        try:
            if code is None or len(code) == 0:
                raise ValidationError(message="List code is required", context="List.addListItem")
            list_info = ListManager.getInfoForList(repo_id, code)
            if list_info is None:
                raise ValidationError(message="List code is invalid", context="List.addListItem")

            if display is None:
                raise ValidationError(message="Display value is required", context="List.addListItem")

            if item_code is None:
                raise ValidationError(message="List Item Code is required", context="List.addListItem")
            if isinstance(code, int):
                item_result = db.run("MATCH (i:ListItem {display: {display}})--(l:List {code: {code}})--(r:Repository) WHERE ID(r) = {repo_id} RETURN ID(i) as id, i.display as display", {"display": display, "code": code, "repo_id": repo_id}).peek()
            else:
                item_result = db.run("MATCH (i:ListItem {display: {display}})--(l:List {code: {code}})--(r:Repository) WHERE ID(r) = {repo_id} RETURN ID(i) as id, i.display as display", {"display": display, "code": code, "repo_id": repo_id}).peek()
            if item_result is not None:
                ret['exists'] = True
                ret['item_id'] = item_result['id']
                ret['display'] = item_result['display']
                return ret
            else:
                item_flds = ["display: {display}", "code: {item_code}", "description: {description}"]
                item_params = {"list_code": code, "repo_id": repo_id, "display": display, "item_code": item_code, "description": description}

                add_result = db.run("MATCH (r:Repository)--(l:List {code: {list_code}}) WHERE ID(r) = {repo_id} CREATE (i:ListItem {" + ", ".join(item_flds) + "})-[:PART_OF]->(l) RETURN ID(i) as id, i.display as display, i.code as code", item_params)


                r = add_result.peek()
                if r:
                    ret['exists'] = False
                    ret['item_id'] = r['id']
                    ret['display'] = r['display']
                    ret['code'] = r['code']
                    return ret
                else:
                    raise DbError(message="Could not add List Item", context="List.addListItem", dberror="")
        except Exception as e:
            raise DbError(message="Could not add List Item", context="List.addListItem", dberror=e.message)

    @staticmethod
    def editListItem(repo_id, code, item_id, display, item_code, description=None):
        try:
            repo_id = int(repo_id)
        except TypeError:
            raise DbError(message="Invalid repo_id provided", context="List.editListItem",
                          dberror="")
        if code is None or len(code) == 0:
            raise ValidationError(message="List code is required", context="List.editListItem")

        if item_code is None or len(item_code) == 0:
            raise ValidationError(message="List item code is required", context="List.editListItem")

        if display is None or len(display) == 0:
            raise ValidationError(message="List Item display is required", context="List.editListItem")

        ret = {}
        result = db.run(
            "MATCH (i:ListItem {code: {item_code}})--(l:List {code: {code}})--(r:Repository) WHERE ID(r) = {repo_id} AND ID(i) <> {item_id}  RETURN ID(i) as id, i.display as display",
            {"item_code": item_code, "code": code, "repo_id": int(repo_id), "item_id": int(item_id)}).peek()
        if result is not None:
            ret['msg'] = "List Item already exists"
            ret['item_id'] = result['id']
            ret['display'] = result['display']
            return ret
        else:
            flds = ["i.display = {display}", "i.code = {item_code}", "i.description = {description}"]
            params = {"code": code, "repo_id": int(repo_id), "display": display, "item_code": item_code, "description": description, "item_id": int(item_id)}
            result = db.run(
                "MATCH (r:Repository)--(l:List {code: {code}})--(i:ListItem) WHERE ID(r) = {repo_id} AND ID(i) = {item_id} SET " + ", ".join(flds) + " RETURN ID(i) as id, i.display as display",
                params)
            r = result.peek()

            # TODO: check query result

            if r:
                ret['item_id'] = r['id']
                ret['display'] = r['display']
                return ret
            else:
                raise DbError(message="Could not edit list item", context="List.editListItem", dberror="")

    @staticmethod
    def deleteListItem(repo_id, code, item_id):
        print repo_id, code, item_id
        try:
            repo_id = int(repo_id)
        except TypeError:
            raise DbError(message="Invalid repo_id provided", context="List.deleteListItem",
                          dberror="")
        try:
            result = db.run(
                "MATCH (r:Repository)--(l:List {code: {code}})-[x]-(i:ListItem) WHERE ID(r) = {repo_id} AND ID(i) = {item_id} DELETE i,x",
                {"repo_id": int(repo_id),  "item_id": int(item_id), "code": code})

            if result is not None:
                return True
            else:
                raise FindError(message="Could not find list item", context="List.deleteListItem", dberror="")
        except Exception as e:
            raise DbError(message="Could not delete list item", context="List.deleteListItem", dberror=e.message)

    @staticmethod
    def getListsForRepo(repo_id):
        repo_id = int(repo_id)
        ret = {'lists': []}
        try:
            lists_res = db.run("MATCH (r:Repository)--(l:List) WHERE ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description as description", {"repo_id": repo_id})
            if lists_res:
                for i_list in lists_res:
                    list_ret = {
                        'id': i_list['id'],
                        'name': i_list['name'],
                        'code': i_list['code'],
                        'description': i_list['description']
                    }
                    ret['lists'].append(list_ret)
                return ret
            else:
                return None
        except Exception as e:
            raise DbError(message="Could not get lists for repo", context="List.getListsForRepo", dberror=e.message)

    @staticmethod
    def getInfoForList(repo_id, code):
        repo_id = int(repo_id)
        try:
            code = int(code)
        except ValueError:
            pass
        try:
            if isinstance(code, int):
                list_res = db.run("MATCH (r:Repository)--(l:List) WHERE ID(l) = {code} AND ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description as description", {"code" :code, "repo_id": repo_id}).peek()
                print list_res
                if list_res is None:
                    return None

                items_res = db.run("MATCH (i:ListItem)--(l:List)--(r:Repository) WHERE ID(l) = {code} AND ID(r) = {repo_id} RETURN ID(i) as id, i.display as display, i.code as code, i.description as description", {"code": code, "repo_id": repo_id})
            else:
                list_res = db.run("MATCH (r:Repository)--(l:List) WHERE l.code = {code} AND ID(r) = {repo_id} RETURN ID(l) as id, l.name as name, l.code as code, l.description as description", {"code" :code, "repo_id": repo_id}).peek()
                print list_res
                if list_res is None:
                    return None

                items_res = db.run("MATCH (i:ListItem)--(l:List)--(r:Repository) WHERE l.code = {code} AND ID(r) = {repo_id} RETURN ID(i) as id, i.display as display, i.code as code, i.description as description", {"code": code, "repo_id": repo_id})

            info = {'list_id': list_res['id'], 'name': list_res['name'], 'code': list_res['code'], 'description': list_res['description']}

            item_list = []
            if items_res:
                for r in items_res:
                    li = {'id': r['id'], 'display': r['display'], 'code': r['code'], 'description': r['description']}
                    item_list.append(li)

            info['items'] = item_list
            return info

        except Exception as e:
            print e.message
            raise DbError(message="Could not get list items for list", context="List.getInfoForList", dberror=e.message)

    #
    # Get number of unique values in a list
    #
    @staticmethod
    def uniqueValueCount(valueSet):
        uValues = set()
        if isinstance(valueSet, list):
            valueSet = set(valueSet)
        for value in valueSet:
            if not isinstance(value, basestring):
                continue
            split_regex = r'[,;|\/]{1}'
            value_array = re.split(split_regex, value)
            for va in value_array:
                uValues.add(va)
        if len(uValues) > 0:
            return len(uValues)
        return False
