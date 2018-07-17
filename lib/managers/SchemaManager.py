from lib.utils.Db import db
import re
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.ValidationError import ValidationError
from lib.exceptions.SettingsValidationError import SettingsValidationError
from pluginbase import PluginBase
from lib.decorators.Memoize import memoized

class SchemaManager:
    plugin_source = PluginBase(package='lib.plugins.dataTypes').make_plugin_source(
        searchpath=['lib/plugins/dataTypes'], identifier='inquisite')

    dataTypePlugins = {}
    dataTypePluginsByPriority = []
    pluginsAreLoaded = False

    def __init__(self):
        pass

    #
    # Get list of data types for defined for a repository
    #
    @staticmethod
    def getTypes(repo_id):
        # TODO validate params

        # TODO: check that repository is owned by current user
        try:
            result = db.run("MATCH (t:SchemaType)--(r:Repository) WHERE ID(r) = {repo_id}  RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"repo_id": int(repo_id)})

            if result:
                typelist = []
                for r in result:
                    t = { 'id': str(r['id']), 'name': r['name'], 'code': r['code'], 'description': r['description']}

                    # get fields
                    i = SchemaManager.getInfoForType(repo_id, r['id'])
                    t["fields"] = i["fields"]

                    typelist.append(t)
                return typelist
        except Exception as e:
            raise DbError(message="Could not get types", context="Schema.getTypes", dberror=e.message)

    #
    # Get specific data type in a repository
    #
    @staticmethod
    def getType(repo_id, schema_id):
        # TODO validate params

        # TODO: check that repository is owned by current user

        try:
            res = db.run("MATCH (r:Repository)--(t:SchemaType) WHERE ID(r) = {repo_id} AND ID(t) = {schema_id}  RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"repo_id": int(repo_id), "schema_id": int(schema_id)}).peek()
            if res:
                t = { 'id': str(res['id']), 'name': res['name'], 'code': res['code'], 'description': res['description']}

                count_res = db.run("MATCH (t:SchemaType)--(d:Data) WHERE ID(t) = {schema_id} RETURN count(d) as data_count", {"schema_id": int(schema_id)}).peek()
                if count_res:
                    t['data_count'] = count_res['data_count']
                else:
                    t['data_count'] = 0

                # get fields
                i = SchemaManager.getInfoForType(repo_id, res['id'])
                t["fields"] = i["fields"]
                return t
        except Exception as e:
            raise DbError(message="Could not get types", context="Schema.getType", dberror=e.message)

    #
    # Return information for a schema type. The type_id parameter can be either a numeric id or string code for the type.
    # Returned value is a dict with keys for type information. A list of fields for the type is under the key "fields"
    #
    @staticmethod
    @memoized
    def getInfoForType(repo_id, type):
        repo_id = int(repo_id)

        # TODO validate params

        try:
            type_id = int(type)
        except Exception:
            type_id = str(type)

        # TODO: check that repository is owned by current user
        try:
            if isinstance(type_id, int):
                tres = db.run(
                    "MATCH (r:Repository)--(t:SchemaType) WHERE ID(t) = {type_id} AND ID(r) = {repo_id} RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"type_id": type_id, "repo_id": repo_id}).peek()

                if tres is None:
                    return None

                result = db.run(
                    "MATCH (f:SchemaField)--(t:SchemaType)--(r:Repository) WHERE ID(t) = {type_id} AND ID(r) = {repo_id} RETURN ID(f) as id, f.name as name, f.code as code, f.type as type, f.description as description, properties(f) as props",
                    {"type_id": int(type_id), "repo_id": repo_id})
            else:
                tres = db.run(
                    "MATCH (r:Repository)--(t:SchemaType) WHERE t.code = {code} AND ID(r) = {repo_id} RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"code": type_id, "repo_id": repo_id}).peek()
                if tres is None:
                    return None

                result = db.run(
                    "MATCH (f:SchemaField)--(t:SchemaType)--(r:Repository) WHERE t.code = {code} AND ID(r) = {repo_id}  RETURN ID(f) as id, f.name as name, f.code as code, f.type as type, f.description as description, properties(f) as props",
                    {"code": type_id, "repo_id": repo_id})

            info = {"type_id": tres['id'], "name": tres['name'], "code": tres['code'],
                    "description": tres['description']}

            fieldlist = []
            if result:
                for r in result:
                    ft = SchemaManager.getDataTypeInstance(r['type'])
                    if ft is None:
                        #raise ValidationError(message="Invalid field type", context="Schema.getFieldsForType")
                        continue

                    t = {'id': str(r['id']), 'name': r['name'], 'code': r['code'], 'description': r['description'], 'type': r['type'], 'settings': {}}

                    dc = SchemaManager.checkFieldForData(repo_id, type_id, r['code'])
                    t['has_data'] = dc['data']

                    for s in ft.getSettingsList():
                        if "settings_" + s in r['props']:
                            t["settings_" + s] = r['props']["settings_" + s]
                            t["settings"][s] = r["props"]["settings_" + s]
                    fieldlist.append(t)
            info["fields"] = fieldlist
            return info
        except Exception as e:
            raise DbError(message="Could not get fields for types", context="Schema.getFieldsForType", dberror=e.message)

    #
    # Get info for field within type
    #
    @staticmethod
    @memoized
    def getInfoForField(repo_id, type_id, field):
        try:
            field_id = int(field)
        except:
            field_id = field.encode('utf-8')

        type_info = SchemaManager.getInfoForType(repo_id, type_id)
        if type_info is None:
            return None

        for f in type_info["fields"]:
            if isinstance(field_id, int) and int(f["id"]) == field_id:
                return f
            elif f["code"] == field_id:
                return f
        return None

    #
    # Check if field has data
    #
    @staticmethod
    @memoized
    def checkFieldForData(repo_id, type_id, field_code):
        try:
            type_id = int(type)
        except Exception:
            type_id = str(type)

        try:
            if isinstance(type_id, int):
                result = db.run("MATCH (r:Repository)--(s:SchemaType)--(d:Data) WHERE ID(r) = {repo_id} AND ID(s) = {type_id} AND d." + field_code + " <> '' return count(d) as data_count", {"repo_id": repo_id, "type_id": type_id}).peek()
            else:
                result = db.run("MATCH (r:Repository)--(s:SchemaType)--(d:Data) WHERE ID(r) = {repo_id} AND s.code = {type_id} AND d." + field_code + " <> '' return count(d) as data_count", {"repo_id": repo_id, "type_id": type_id}).peek()
            if result is not None:
                data_count = result['data_count']
                ret = {"data": False, "total": data_count}
                if data_count > 0:
                    ret['data'] = True
                return ret
        except Exception as e:
            raise DbError(message="Could not get data count: " + e.message, context="Schema.checkFieldForData",
                          dberror=e.message)

    #
    #
    #
    @staticmethod
    def addType(repo_id, name, code, description, fields):
        # TODO validate params

        # TODO: check that repository is owned by current user
        ret = { "exists": False}
        try:
            result = db.run("MATCH (t:SchemaType{code: {code}})--(r:Repository) WHERE ID(r) = {repo_id}  RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"code": code, "repo_id": int(repo_id)})
            if result is not None and len(list(result)):
               ret = { "exists": True }
               for r in result:
                   ret['type'] = {
                       "id": r['id'],
                       "name": r['name'],
                       "code": r['code'],
                       "description": r['description']
                   }

               return ret
            else:
                result = db.run("MATCH (r:Repository) WHERE ID(r) = {repo_id} CREATE (t:SchemaType { name: {name}, code: {code}, description: {description}, storage: 'Graph'})-[:PART_OF]->(r) RETURN ID(t) as id",
                            {"repo_id": int(repo_id),"name": name, "code": code, "description": description})

            SchemaManager.resetTypeInfoCache()
        except Exception as e:
            raise DbError(message="Could not add type: " + e.message, context="Schema.addType",
                          dberror=e.message)

        # add/edit fields
        field_status = {}
        settings =  {f.replace("settings_", ""):v for f,v in fields.iteritems() if 'settings_' in f}

        for k in fields:

            # add field
            fret = SchemaManager.addField(repo_id, code, k['name'], k['code'], k['type'], k['description'], settings)

            if 'field_id' in fret:
                field_status[k['code']] = {'status_code': 200, 'field_id': fret['field_id'], 'msg': 'Created new field'}
            else:
                field_status[k['code']] = {'status_code': 200, 'field_id': None, 'msg': 'Could not create new field'}

        if result:
            for r in result:
                ret['type'] = {
                    "id": r['id'],
                    "name": name,
                    "code": code,
                    "description": description,
                    "field_status": field_status
                }
                break
        else:
            raise DbError(message="Could not add type", context="Schema.addType",
                          dberror="")


        return ret

    @staticmethod
    def editType(repo_id, type_id, name, code, description, fields, fieldsToDelete):
        # TODO validate params

        # TODO: check that repository is owned by current user


        result = db.run(
            "MATCH (r:Repository)--(t:SchemaType) WHERE ID(r) = {repo_id} AND ID(t) = {type_id} SET t.name = {name}, t.code = {code}, t.description = {description} RETURN ID(t) AS id",
            {"repo_id": int(repo_id), "type_id": int(type_id), "name": name, "code": code, "description": description})

        # add/edit fields
        field_status = {}
        for k in fields:
            settings = {f.replace("settings_", ""): v for f, v in fields[k].iteritems() if 'settings_' in f}
            if 'id' in fields[k]:
                # edit existing field
                fret = SchemaManager.editField(repo_id, code, fields[k].get('id', ''), fields[k].get('name', ''), fields[k].get('code', ''), fields[k].get('type', ''),
                                               fields[k]['description'], settings)

                if 'field_id' in fret:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': fret['field_id'],
                                                       'msg': 'Edited field'}
                else:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': None,
                                                       'msg': 'Could not edit field'}
            else:
                # add field
                fret = SchemaManager.addField(repo_id, code, fields[k].get('name', ''), fields[k].get('code', ''), fields[k].get('type', ''), fields[k].get('description', ''), settings)

                if 'field_id' in fret:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': fret['field_id'], 'msg': 'Created new field'}
                else:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': None, 'msg': 'Could not create new field'}

        # delete fields
        if fieldsToDelete:
            for field_id in fieldsToDelete:
                SchemaManager.deleteField(repo_id, code, field_id)


        SchemaManager.resetTypeInfoCache()

        if result:
            ret = {}
            for r in result:
                ret['type'] = {
                    "id": r['id'],
                    "name": name,
                    "code": code,
                    "description": description,
                    "field_status": field_status
                }
                return ret
        else:
            raise DbError(message="Could not edit type", context="Schema.editType",
                          dberror="")

    @staticmethod
    def deleteType(repo_id, type_id):
        # TODO validate params

        # TODO: check that repository is owned by current user

        try:
            result = db.run("MATCH (t:SchemaType)-[x]-(r:Repository) WHERE ID(r) = {repo_id} AND ID(t) = {type_id} OPTIONAL MATCH (f:SchemaField)-[y]-(t) DELETE x,y,t,f",
                            {"type_id": int(type_id), "repo_id": int(repo_id)})

            if result is not None:
                SchemaManager.resetTypeInfoCache()
                return {"type_id": type_id}
            else:
                raise FindError(message="Could not find type", context="Schema.deleteType", dberror="")
        except Exception as e:
            raise DbError(message="Could not delete type", context="Schema.deleteType", dberror=e.message)

    @staticmethod
    def addField(repo_id, typecode, name, code, fieldtype, description, settings):
        # TODO validate params
        if typecode is None or len(typecode) == 0:
            raise ValidationError(message="Type code is required", context="Schema.addField")

        type_info = SchemaManager.getInfoForType(repo_id, typecode)
        SchemaManager.resetTypeInfoCache()

        if type_info is None:
            raise ValidationError(message="Type code is invalid", context="Schema.addField")
        typecode = type_info["code"]    # always use code

        if code is None or len(code) == 0:
            raise ValidationError(message="Field code is required", context="Schema.addField")

        if name is None or len(name) == 0:
            raise ValidationError(message="Field name is required", context="Schema.addField")

        # Check field type
        if fieldtype not in SchemaManager.getDataTypes():
            raise ValidationError(message="Invalid field type", context="Schema.addField")

        ret = {}
        ft = SchemaManager.getDataTypeInstance(fieldtype)
        if ft is None:
            raise ValidationError(message="Invalid field type", context="Schema.addField")

        sv = ft.validateSettings(settings)
        if sv is not True:
            raise SettingsValidationError(message="Invalid field type", errors={code: sv}, context="Schema.addField")


        # TODO: check that repository is owned by current user

        result = db.run(
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repo_id}  RETURN f.name as name, ID(f) as id",
            {"typecode": typecode, "code": code, "repo_id": int(repo_id)}).peek()
        if result is not None:
            ret['exists'] = True
            ret['field_id'] = result['id']
            ret['name'] = result['name']
            return ret
        else:
            flds = ["name: {name}", "code: {code}", "description: {description}", "type: {fieldtype}"]
            params =  {"repo_id": int(repo_id), "name": name, "code": code, "description": description,
                 "typecode": typecode, "fieldtype": fieldtype}
            for s in settings:
                flds.append("settings_" + s + ": {settings_" + s + "}")
                params["settings_" + s] = settings[s]

            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}}) WHERE ID(r) = {repo_id} CREATE (f:SchemaField { " + ", ".join(flds) + " })-[:PART_OF]->(t) RETURN ID(f) as id, f.name as name, f.code as code",
                params)

            r = result.peek()
            # TODO: check query result
            if r:
                ret['exists'] = False
                ret['field_id'] = r['id']
                ret['name'] = r['name']
                ret['code'] = r['code']
                return ret
            else:
                raise DbError(message="Could not add field", context="Schema.addField", dberror="")


    @staticmethod
    def editField(repo_id, typecode, field_id, name, code, fieldtype, description, settings):
        if code is None or len(code) == 0:
            raise ValidationError(message="Field code is required", context="Schema.editField")

        if name is None or len(name) == 0:
            raise ValidationError(message="Field name is required", context="Schema.editField")


        ret = {}

        # Check field type
        if fieldtype not in SchemaManager.getDataTypes():
            raise ValidationError(message="Invalid field type " + fieldtype, context="Schema.editField")

        ft = SchemaManager.getDataTypeInstance(fieldtype)
        if ft is None:
            raise ValidationError(message="Invalid field type " + fieldtype, context="Schema.editField")

        sv = ft.validateSettings(settings)
        if sv is not True:
            raise SettingsValidationError(message="Invalid settings for field " + name, errors={code: sv}, context="Schema.editField")

        # TODO: check that repository is owned by current user
        SchemaManager.resetTypeInfoCache()

        result = db.run(
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repo_id} AND ID(f) <> {field_id}  RETURN ID(f) as id, f.name as name",
            {"typecode": typecode, "code": code, "repo_id": int(repo_id), "field_id": int(field_id)}).peek()
        if result is not None:
            ret['msg'] = "Field already exists"
            ret['field_id'] = result['id']
            ret['name'] = result['name']
            return ret
        else:
            flds = ["f.name = {name}", "f.code = {code}", "f.description = {description}", "f.type = {fieldtype}"]
            params = {"repo_id": int(repo_id), "name": name, "code": code, "description": description,
                 "typecode": typecode, "fieldtype": fieldtype, "field_id": int(field_id)}

            for s in settings:
                flds.append("f.settings_" + s + " = {settings_" + s + "}")
                params["settings_" + s] = settings[s]

            #if fieldtype == 'ListDataType':
                # TODO Delete data that doesn't exist in new datatype unless the merge setting is allowed.

            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}})--(f:SchemaField) WHERE ID(r) = {repo_id} AND ID(f) = {field_id} SET " + ", ".join(flds) + " RETURN ID(f) as id, f.name as name",
                params)
            r = result.peek()

            # TODO: check query result

            if r:
                ret['field_id'] = r['id']
                ret['name'] = r['name']
                return ret
            else:
                raise DbError(message="Could not edit field", context="Schema.editField", dberror="")


    @staticmethod
    def deleteField(repo_id, typecode, field_id):
        # TODO validate params


        # TODO: check that repository is owned by current user
        SchemaManager.resetTypeInfoCache()

        try:
            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}})-[x]-(f:SchemaField) WHERE ID(r) = {repo_id} AND ID(f) = {field_id} DELETE f,x",
                {"repo_id": int(repo_id),  "field_id": int(field_id), "typecode": typecode})

            if result is not None:
                return True
            else:
                raise FindError(message="Could not find field", context="Schema.deleteField", dberror="")
        except Exception as e:
            raise DbError(message="Could not delete field", context="Schema.deleteField", dberror=e.message)

    #
    #
    #
    @classmethod
    def loadDataTypePlugins(cls):
        byPriority = {}
        for n in cls.plugin_source.list_plugins():
            if re.match("Base", n):
                continue
            c = getattr(cls.plugin_source.load_plugin(n), n)
            cls.dataTypePlugins[n] = c
            byPriority[c.priority] = n

        for x in sorted(byPriority.iteritems()):
            cls.dataTypePluginsByPriority.append(x[1])
        cls.pluginsAreLoaded = True
        return True

    #
    #
    #
    @classmethod
    @memoized
    def getDataTypes(cls):
        if cls.pluginsAreLoaded is False:
            cls.loadDataTypePlugins()
        return cls.dataTypePluginsByPriority

    #
    #
    #
    @classmethod
    @memoized
    def getInfoForDataTypes(cls):
        if cls.pluginsAreLoaded is False:
            cls.loadDataTypePlugins()
        types = {}
        for x in SchemaManager.getDataTypes():
            p = SchemaManager.getDataTypePlugin(x)
            types[x] = { "name": p.name, "description": p.description, "settings": p.getSettingsList(), "order": p.getSettingsOrder() }
        return types

    #
    #
    #
    @classmethod
    @memoized
    def getDataTypePlugin(cls, n):
        if cls.pluginsAreLoaded is False:
            cls.loadDataTypePlugins()
        if n in cls.dataTypePlugins:
            return cls.dataTypePlugins[n]
        return None

    #
    #
    #
    @classmethod
    @memoized
    def getDataTypeInstance(cls, n):
        if cls.pluginsAreLoaded is False:
           cls.loadDataTypePlugins()
        if n in cls.dataTypePlugins:
            return cls.dataTypePlugins[n]()
        return None

    #
    #
    #
    @classmethod
    @memoized
    def getDataTypeInstanceForField(cls, repo_id, type_code, field_code, value=None):
        field_info = SchemaManager.getInfoForField(repo_id, type_code, field_code)
        if field_info is None:
            # TODO: throw exception?
            return None

        ft = SchemaManager.getDataTypeInstance(field_info["type"])
        if ft is None:
            # TODO: throw exception?
            return None
        ft.setSettings(field_info["settings"])
        if value is not None:
            ft.set(value)
        return ft

    #
    #
    #
    @classmethod
    def resetTypeInfoCache(cls):
        SchemaManager.getInfoForType.reset()
        SchemaManager.getInfoForField.reset()
        SchemaManager.getDataTypeInstanceForField.reset()
