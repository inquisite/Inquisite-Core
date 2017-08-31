from lib.utils.Db import db
import re
from lib.exceptions.FindError import FindError
from lib.exceptions.DbError import DbError
from lib.exceptions.ValidationError import ValidationError
from pluginbase import PluginBase

class SchemaManager:
    plugin_source = PluginBase(package='lib.plugins.dataTypes').make_plugin_source(
        searchpath=['lib/plugins/dataTypes'], identifier='inquisite')

    FieldTypes = [] #self.getDataTypes()
    dataTypePlugins = {}
    pluginsAreLoaded = False

    def __init__(self):
        pass

    # Return repository name and id for given repo code
    @staticmethod
    def getRepositoryByCode(code):
        result = db.run(
            "MATCH (r:Repository {name: {code}}) RETURN ID(r) AS id, r.name AS  name",
            {"code": code})

        ret = {}

        if result:
            for r in result:
                ret['repository_id'] = r['id']
                ret['name'] = r['name']
                return ret
        else:
            raise FindError("Could not find repository")

        return ret

    # Get list of data types for repository
    @staticmethod
    def getTypes(repository_id):
        # TODO validate params

        # TODO: check that repository is owned by current user

        try:
            result = db.run("MATCH (t:SchemaType)--(r:Repository) WHERE ID(r) = {repository_id}  RETURN ID(t) as id, t.name as name, t.code as code, t.description as description", {"repository_id": int(repository_id)})

            if result:
                typelist = []
                for r in result:
                    t = { 'id': str(r['id']), 'name': r['name'], 'code': r['code'], 'description': r['description']}
                    # get fields
                    t['fields'] = SchemaManager.getFieldsForType(r['id'])

                    typelist.append(t)
                return typelist
        except Exception as e:
            raise DbError(message="Could not get types", context="Schema.getTypes", dberror=e.message)

    @staticmethod
    def getFieldsForType(type_id):
        # TODO validate params

        # TODO: check that repository is owned by current user

        try:
            result = db.run(
                "MATCH (f:SchemaField)--(t:SchemaType) WHERE ID(t) = {type_id}  RETURN ID(f) as id, f.name as name, f.code as code, f.type as type, f.description as description",
                {"type_id": int(type_id)})

            fieldlist = []
            if result:
                for r in result:
                    t = {'id': str(r['id']), 'name': r['name'], 'code': r['code'], 'description': r['description'], 'type': r['type']}

                    fieldlist.append(t)

            return fieldlist
        except Exception as e:
            raise DbError(message="Could not get fields for types", context="Schema.getFieldsForType", dberror=e.message)

    @staticmethod
    def addType(repository_id, name, code, description, fields):
        # TODO validate params

        # TODO: check that repository is owned by current user
        ret = { "exists": False}
        try:
            result = db.run("MATCH (t:SchemaType{code: {code}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN t.id as id, t.name as name, t.code as code, t.description as description", {"code": code, "repository_id": int(repository_id)}).peek()
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
                result = db.run("MATCH (r:Repository) WHERE ID(r) = {repository_id} CREATE (t:SchemaType { name: {name}, code: {code}, description: {description}, storage: 'Graph' })-[:PART_OF]->(r) RETURN ID(t) as id",
                            {"repository_id": int(repository_id),"name": name, "code": code, "description": description})
        except Exception as e:
            raise DbError(message="Could not add type", context="Schema.addType",
                          dberror=e.message)

        # add/edit fields
        field_status = {}
        for k in fields:
            # add field
            fret = SchemaManager.addField(repository_id, code, k['name'], k['code'], k['type'], k['description'])

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
    def editType(repository_id, type_id, name, code, description, fields, fieldsToDelete):
        # TODO validate params

        # TODO: check that repository is owned by current user


        result = db.run(
            "MATCH (r:Repository)--(t:SchemaType) WHERE ID(r) = {repository_id} AND ID(t) = {type_id} SET t.name = {name}, t.code = {code}, t.description = {description} RETURN ID(t) AS id",
            {"repository_id": int(repository_id), "type_id": int(type_id), "name": name, "code": code, "description": description})

        # add/edit fields
        field_status = {}
        for k in fields:
            if 'id' in fields[k]:
                # edit existing field
                fret = SchemaManager.editField(repository_id, code, fields[k]['id'], fields[k]['name'], fields[k]['code'], fields[k]['type'],
                                               fields[k]['description'])

                if 'field_id' in fret:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': fret['field_id'],
                                                       'msg': 'Edited field'}
                else:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': None,
                                                       'msg': 'Could not edit field'}
            else:
                # add field
                fret = SchemaManager.addField(repository_id, code, fields[k]['name'], fields[k]['code'], fields[k]['type'], fields[k]['description'])

                if 'field_id' in fret:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': fret['field_id'], 'msg': 'Created new field'}
                else:
                    field_status[fields[k]['code']] = {'status_code': 200, 'field_id': None, 'msg': 'Could not create new field'}

        # delete fields
        if fieldsToDelete:
            for field_id in fieldsToDelete:
                SchemaManager.deleteField(repository_id, code, field_id)


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
    def deleteType(repository_id, type_id):
        # TODO validate params

        # TODO: check that repository is owned by current user

        try:
            result = db.run("MATCH (t:SchemaType)-[x]-(r:Repository) WHERE ID(r) = {repository_id} AND ID(t) = {type_id} optional match (f:SchemaField)-[y]-(t) DELETE x,y,t,f",
                            {"type_id": int(type_id), "repository_id": int(repository_id)})
            if result is not None:
                return True
            else:
                raise FindError(message="Could not find type", context="Schema.deleteType", dberror="")
        except Exception as e:
            raise DbError(message="Could not delete type", context="Schema.deleteType", dberror=e.message)

    @staticmethod
    def addField(repository_id, typecode, name, code, fieldtype, description):
        # TODO validate params

        # Check field type
        if fieldtype not in SchemaManager.FieldTypes:
            raise ValidationError(message="Invalid field type", context="Schema.addField")

        ret = {}

        # TODO: check that repository is owned by current user

        result = db.run(
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repository_id}  RETURN f.name as name, ID(f) as id",
            {"typecode": typecode, "code": code, "repository_id": int(repository_id)}).peek()
        if result is not None:
            r = result.peek()
            ret['exists'] = True
            ret['field_id'] = r['id']
            ret['name'] = r['name']
            return ret
        else:
            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}}) WHERE ID(r) = {repository_id} CREATE (f:SchemaField { name: {name}, code: {code}, description: {description}, type: {fieldtype} })-[:PART_OF]->(t) RETURN ID(f) as id, f.name as name",
                {"repository_id": int(repository_id), "name": name, "code": code, "description": description,
                 "typecode": typecode, "fieldtype": fieldtype})
            r = result.peek()

            # TODO: check query result

            if r:
                ret['exists'] = False
                ret['field_id'] = r['id']
                ret['name'] = r['name']
                return ret
            else:
                raise DbError(message="Could not add field", context="Schema.addField", dberror="")


    @staticmethod
    def editField(repository_id, typecode, field_id, name, code, fieldtype, description):
        # TODO validate params


        ret = {}

        # Check field type
        if fieldtype not in SchemaManager.FieldTypes:
            raise ValidationError(message="Invalid field type", context="Schema.addField")

        # TODO: check that repository is owned by current user

        result = db.run(
            "MATCH (f:SchemaField {code: {code}})--(t:SchemaType {code: {typecode}})--(r:Repository) WHERE ID(r) = {repository_id} AND ID(f) <> {field_id}  RETURN ID(f) as id, f.name as name",
            {"typecode": typecode, "code": code, "repository_id": int(repository_id), "field_id": int(field_id)}).peek()
        if result is not None:
            r = result.peek()
            ret['msg'] = "Field already exists"
            ret['field_id'] = r['id']
            ret['name'] = r['name']
            return ret
        else:
            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}})--(f:SchemaField) WHERE ID(r) = {repository_id} AND ID(f) = {field_id} SET f.name = {name}, f.code = {code}, f.description = {description}, f.type = {fieldtype} RETURN ID(f) as id, f.name as name",
                {"repository_id": int(repository_id), "name": name, "code": code, "description": description,
                 "typecode": typecode, "fieldtype": fieldtype, "field_id": int(field_id)})
            r = result.peek()

            # TODO: check query result

            if r:
                ret['field_id'] = r['id']
                ret['name'] = r['name']
                return ret
            else:
                raise DbError(message="Could not edit field", context="Schema.editField", dberror="")


    @staticmethod
    def deleteField(repository_id, typecode, field_id):
        # TODO validate params


        # TODO: check that repository is owned by current user


        try:
            result = db.run(
                "MATCH (r:Repository)--(t:SchemaType {code: {typecode}})-[x]-(f:SchemaField) WHERE ID(r) = {repository_id} AND ID(f) = {field_id} DELETE f,x",
                {"repository_id": int(repository_id),  "field_id": int(field_id), "typecode": typecode})

            if result is not None:
                return True
            else:
                raise FindError(message="Could not find field", context="Schema.deleteField", dberror="")
        except Exception as e:
            raise DbError(message="Could not delete field", context="Schema.deleteField", dberror=e.message)

    @staticmethod
    def createDataTypeFromFields(repository_id, typecode, field_names):
        typecode_proc = re.sub(r"[^A-Za-z0-9_]", "_", typecode)[0:15].strip()
        typecode_proc_disp = re.sub(r"[_]", " ", typecode_proc).strip()
        field_spec = []
        for f in field_names:
            fproc = re.sub(r'[^A-Za-z0-9_]+', '_', f).lower()
            fproc_disp = re.sub(r'[_]+', ' ', fproc).title()
            field_spec.append({
                'name': fproc_disp,
                'code': fproc,
                'description': 'Created by data import',
                'type': 'TEXT'  # TODO: support other types
            })

        SchemaManager.addType(repository_id, typecode_proc_disp, typecode_proc, "Created by data import", field_spec)

        return field_names

    @staticmethod
    def addDataToRepo(repository_id, typecode, data):

        typecode_proc = re.sub(r"[^A-Za-z0-9_]", "_", typecode)[0:15].strip()

        # TODO: check that repository is owned by current user

        # TODO: verify fields present are valid for this type
        # TODO: validate each field value

        flds = []
        for i in data.keys():
            if (i == '_ID'):
                continue
            fname = re.sub(r"[^A-Za-z0-9_]", "_", i)        # remove non-alphanumeric characters from field names
            fname = re.sub(r"^([\d]+)", "_\1", fname).strip()      # Neo4j field names cannot start with a number; prefix such fields with an underscore


            flds.append(fname + ":{" + fname + "}")
            data[fname] = data[i]                           # add "data" entry with neo4j-ready field name


        data['repository_id'] = int(repository_id)
        data['typecode_proc'] = typecode_proc

        q = "MATCH (t:SchemaType{code: {typecode_proc}}) CREATE (n:Data {" + ",".join(flds) + "})-[:IS]->(t) RETURN ID(n) as id"

        try:
            result = db.run(q, data)
        except Exception as e:
            raise DbError(message="Could not create data", context="Schema.addDataToRepo", dberror=e.message)
        id = None

        for record in result:
            id = record['id']

        node_created = False
        summary = result.consume()
        if summary.counters.nodes_created >= 1:

            if id is not None:

                #result = utils.run("MATCH (r:Repository), (d:Data) WHERE ID(d) = " + str(id) + " AND ID(r)= {repository_id} CREATE (r)<-[:PART_OF]-(d)", data)

                rel_created = False
                #summary = result.consume()
                if summary.counters.relationships_created >= 1:
                    rel_created = True

                if rel_created:
                    return True
                else:
                    return False

    #
    #
    #
    @classmethod
    def loadDataTypePlugins(cls):
        for n in cls.plugin_source.list_plugins():
            if re.match("Base", n):
                continue
            c = getattr(cls.plugin_source.load_plugin(n), n)
            cls.dataTypePlugins[n] = c

        cls.pluginsAreLoaded = True
        return True

    #
    #
    #
    @classmethod
    def getDataTypes(cls):
        if cls.pluginsAreLoaded is False:
            cls.loadDataTypePlugins()
        return cls.dataTypePlugins.keys()

    #
    #
    #
    @classmethod
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
    def getDataTypeInstance(cls, n):
        if cls.pluginsAreLoaded is False:
           cls.loadDataTypePlugins()
        if n in cls.dataTypePlugins:
            return cls.dataTypePlugins[n]()
        return None