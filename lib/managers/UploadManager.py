import os
import os.path
import hashlib
from lib.utils.Db import db
from flask import Blueprint, request, session
from lib.exceptions.UploadError import UploadError
from lib.exceptions.ImportError import ImportError
from lib.utils.FileHelpers import getMimetypeForFile
from lib.managers.DataManager import DataManager
from lib.managers.SchemaManager import SchemaManager
from lib.managers.ListManager import ListManager
from lib.managers.DataReaderManager import DataReaderManager
from lib.managers.AnalyzerManager import AnalyzerManager
from api.sockets.socket_resp import pass_message
import time
import humanize
import re
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/../../uploads"
ALLOWED_MIMETYPES = ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/plain', 'text/json']

class UploadManager:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    # Analyze uploaded file, determine file type and stash in file store
    #
    @staticmethod
    def processUpload(repo_id):
        if 'data_file' not in request.files:
            raise UploadError(message="File not found", context="UploadManager.processUpload")

        input_file = request.files['data_file']


        if input_file:
            original_filename = input_file.filename
            hash_object = hashlib.sha256(original_filename)
            filename = "repo_" + str(repo_id) + "_" + hash_object.hexdigest()

            upload_filepath = os.path.join(UPLOAD_FOLDER, filename)
            pass_message('upload_step', {"step": "Uploading File", "pos": 10})
            try:
                input_file.save(upload_filepath)
            except Exception as e:
                raise UploadError(message="Could not write uploaded file: " + e.message,
                                  context="UploadManager.processUpload")

            mimetype = getMimetypeForFile(upload_filepath)
            if mimetype is None:
                os.remove(upload_filepath)
                raise UploadError(message="Unrecognized file", context="UploadManager.processUpload")

            if UploadManager.allowed_file(mimetype) is False:
                os.remove(upload_filepath)
                raise UploadError(message="File type " + mimetype + " is not allowed",
                                  context="UploadManager.processUpload")
            pass_message('upload_step', {"step": "Generating Preview", "pos": 20})
            pass_message('upload_status', {"status": "Starting Preview", "pos": 0})
            preview = UploadManager._generatePreview(filepath=upload_filepath, mimetype=mimetype)
            pass_message('upload_step', {"step": "Generating Analysis", "pos": 30})
            pass_message('upload_status', {"status": "Starting Analysis", "pos": 0})
            rowCount, columnCount, columns, stats, recommendedSchema = UploadManager._generateAnalysis(repo_id=repo_id, filepath=upload_filepath, mimetype=mimetype)
            pass_message('upload_step', {"step": "Upload Complete", "pos": 100})
            return {
                "filesize": os.path.getsize(upload_filepath),
                "filename": filename,
                "original_filename": original_filename,
                "mimetype": mimetype,
                "preview": preview,
                "total_columns": columnCount,
                "total_rows": rowCount,
                "column_stats": stats,
                "recommended_schema": recommendedSchema
            }


        raise UploadError(message="No file uploaded", context="UploadManager.processUpload")


    #
    # Generate preview data for file
    #
    @staticmethod
    def _generatePreview(filepath, mimetype, rows=100, start=0):
        data = []
        headers = []

        try:
            start = int(start)
        except:
            start = 0


        reader = DataReaderManager.identify(filepath)
        if reader is not None:
            # TODO: set preview type from reader
            preview_type = "table"

            # TODO: error checking
            reader.read(filepath)
            data = reader.getRows(rows=rows, start=start)
            headers = reader.getHeaders()
        else:
            raise UploadError(message="Cannot extract preview data for unsupported file type " + mimetype,
                              context="UploadManager._generatePreview")
        return {"headers": headers, "data": data, "preview_type": preview_type, "type": reader.type}

    @staticmethod
    def _generateAnalysis(repo_id, filepath, mimetype):
        data = []
        headers = []

        reader = DataReaderManager.identify(filepath)
        if reader is not None:
            reader.read(filepath)
            data = reader.getRows()
            headers = reader.getHeaders()
            rowCount = len(data)
            readerName = reader.getPluginName()
            columnCount, columns, stats, recommendedSchema = AnalyzerManager.createAnalysis(repo_id, data, rowCount, headers, readerName)
            return rowCount, columnCount, columns, stats, recommendedSchema
        else:
            raise UploadError(message="Cannot analyze data from unsupported file type" + mimetype, context="UploadManager._generatePreview")


    #
    #
    #
    @staticmethod
    def allowed_file(mimetype):
        return mimetype in ALLOWED_MIMETYPES

    #
    #
    #
    @staticmethod
    def importData(repo_id, type, filename, original_filename, data_mapping, ignore_first, field_names, schema_name, data_types, field_descriptions, search_display_fields, allow_list_merge, start=0):
        upload_filepath = os.path.join(UPLOAD_FOLDER, filename)
        mt = getMimetypeForFile(upload_filepath)
        pass_message('import_step', {"step": "Gathering data", "pos": 25})
        data = UploadManager._generatePreview(filepath=upload_filepath, mimetype=mt, rows=1000000, start=start)
        if data is None:
            raise ImportError(message="Could not read file", context="UploadManager.importData")
        pass_message('import_step', {"step": "Getting/Generating Schema", "pos": 50})
        if str(type) == "-1":
            # create type
            if schema_name:
                schema_type = re.sub(r'[^A-Za-z0-9_]+', '_', schema_name).lower()
            else:
                schema_name = 'new type'
                schema_type = 'new_type'

            # Check for exisiting type and iterate over _n suffixes until we find one that doesn't exist
            existing_type = SchemaManager.getInfoForType(repo_id, schema_type)
            if existing_type:
                i = 1
                while True:
                    tmp_schema_name = schema_name + '_'+str(i)
                    tmp_schema_type = schema_type + '_'+str(i)
                    existing_type = SchemaManager.getInfoForType(repo_id, tmp_schema_type)
                    if not existing_type:
                        break
                    i += 1
                schema_name = tmp_schema_name
                schema_type = tmp_schema_type
            new_type = SchemaManager.addType(repo_id, schema_name, schema_type, "Type created by import", {})
            if "type" in new_type:
                type = new_type["type"]["code"]

        SchemaManager.resetTypeInfoCache()
        type_info = SchemaManager.getInfoForType(repo_id, type)
        if type_info is None:
            raise ImportError(message="Invalid type", context="UploadManager.importData")
        typecode = type_info["code"]

        fields_created = {}
        # create new fields
        for i, m in enumerate(data_mapping):
            # skip empty types
            if len(data_types[i]) == 0:
                continue
            try:
                fid = int(m)
                field_info = SchemaManager.getInfoForField(repo_id, type, fid)
                if field_info is None:
                    data_mapping[i] = 0 # invalid field - don't import
                else:
                    data_mapping[i] = field_info["code"]
            except Exception as e:
                # is not id... does field with this code exist?
                if field_names[i] != data_mapping[i] and field_names[i] != '' and field_names[i] is not None:
                    m = field_names[i]
                mCode = re.sub(r'[^A-Za-z0-9_]+', '_', m).lower()
                if len(mCode) == 0:
                    continue
                data_mapping[i] = mCode
                field_info = SchemaManager.getInfoForField(repo_id, type, m)
                if field_info is None:
                    # create new field
                    mField = ''
                    if field_descriptions[i]:
                        mField = field_descriptions[i]
                    settings = {"search_display": search_display_fields[i]}
                    if data_types[i] == 'ListDataType':
                        merge_setting = search_display_fields[i]
                        new_list = ListManager.addList(repo_id, m, mCode+'_list', merge_setting)
                        if new_list:
                            list_code = new_list['code']
                        else:
                            list_code = None
                        settings['list_code'] = list_code

                    new_field = SchemaManager.addField(repo_id, type, m, mCode, data_types[i], mField, settings)
                    if new_field is not None:
                        data_mapping[i] = new_field["code"]
                        fields_created[new_field["code"]] = new_field
                    else:
                        data_mapping[i] = 0
                else:
                    # set mapping to use field code
                    data_mapping[i] = field_info["code"]

        SchemaManager.resetTypeInfoCache()
        type_info = SchemaManager.getInfoForType(repo_id, type)
        fieldmap = {}
        for v in type_info["fields"]:
            fieldmap[v["code"]] = v

        data_mapping = map(lambda x: str(x), data_mapping)
        import_rows = len(data["data"])
        num_errors = 0
        errors = {}
        counts = {'type': typecode, 'total': 0, 'source_total': import_rows}

        # TODO: record original file name, file size, file type
        upload_uuid = UploadManager.createImportEvent(repo_id, type_info["code"], upload_filepath, original_filename, data["type"], import_rows)
        pass_message('import_step', {"step": "Importing Data", "pos": 75})
        cell_chunk = 100/float(import_rows)
        import_display = 0
        error_display = 0
        timer = time.time()
        for line, r in enumerate(data["data"]):
            if time.time() > timer+0.5:
                pass_message('import_status', {"status": "Importing Row " + str(line), "pos": import_display})
                timer = time.time()
            import_display += cell_chunk
            fields = {}
            for i, fid in enumerate(data_mapping):
                if fid not in fieldmap:
                    continue
                if isinstance(r, list):
                    fields[fid] = r[i]
                    continue
                if data["headers"][i] not in r:
                    continue
                if r[data["headers"][i]] and r[data["headers"][i]] != '':
                    fields[fid] = r[data["headers"][i]]
                else:
                    fields[fid] = None
            try:
                DataManager.add(repo_id, type, fields, upload_uuid, fields_created)
                counts['total'] = counts['total'] + 1
            except Exception as e:
                if line not in errors:
                    errors[line] = []
                errors[line].append(e.message)
                num_errors = num_errors + 1
                pass_message('error_status', {"status": "Error in Row " + str(line) + ": " + e.message, "pos": error_display})
                error_display += cell_chunk

        UploadManager.closeImportEvent(upload_uuid)
        pass_message('import_step', {"step": "Import Complete", "pos": 100})
        return {"errors": errors, "error_count": num_errors, "mapping": data_mapping,
                "fields_created": fields_created, "counts": counts, "filename": filename}

    @staticmethod
    def createImportEvent(repo_id, type, upload_filepath, original_filename, ftype, row_count):
        result = db.run(
            "MATCH (r:Repository) WHERE ID(r) = {repo_id} CREATE (e:ImportEvent { original_filename: {original_filename}, type: {type}, filetype: {filetype}, size: {size}, rows: {rows}, started_on: {time}, ended_on: null})-[:IMPORTED_INTO]->(r) RETURN ID(e) AS id",
            {"repo_id": int(repo_id), "original_filename": original_filename, "type": type, "filetype": ftype, "size": os.path.getsize(upload_filepath), "rows": row_count, "time": time.time()})
        if result is None:
            return False
        r = result.peek()

        # We have to do a separate query because Neo4j doesn't make the uuid available on CREATE (argh)
        result = db.run(
            "MATCH (e:ImportEvent) WHERE ID(e) = {id} RETURN e.uuid AS uuid",
            {"id": int(r['id'])})
        if result is None:
            return False

        r = result.peek()
        if r and 'uuid' in r:
            return r['uuid']
        return True

    @staticmethod
    def closeImportEvent(uuid):
        result = db.run(
            "MATCH (e:ImportEvent { uuid: {uuid}}) SET e.ended_on = {time} RETURN e.uuid as uuid",
            {"uuid": uuid, "time": time.time()})
        if result is None:
            return False
        r = result.peek()
        if r and 'uuid' in r:
            return r['uuid']
        return True

    @staticmethod
    def getImportEventsForRepo(repo_id):
        result = db.run(
            "MATCH (r:Repository)--(e:ImportEvent) WHERE ID(r) = {repo_id} RETURN ID(e) AS id, properties(e) AS props ORDER BY e.started_on",
            {"repo_id": int(repo_id)})
        if result is None:
            return False

        events = []
        for r in result:
            l = r['props']
            l['id'] = r['id']
            l['size_display'] = humanize.naturalsize(l['size'])
            l['started_on'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(l['started_on']))
            l['ended_on'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(l['ended_on']))
            events.append(l)
        return events
