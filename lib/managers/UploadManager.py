import os
import os.path
import hashlib
from lib.utils.Db import db
from flask import Blueprint, request
from lib.exceptions.UploadError import UploadError
from lib.exceptions.ImportError import ImportError
from lib.utils.FileHelpers import getMimetypeForFile
from lib.managers.DataManager import DataManager
from lib.managers.SchemaManager import SchemaManager
from lib.managers.DataReaderManager import DataReaderManager
from lib.managers.AnalyzerManager import AnalyzerManager
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

            preview = UploadManager._generatePreview(filepath=upload_filepath, mimetype=mimetype)
            rowCount, columnCount, columns, stats, recommendedSchema = UploadManager._generateAnalysis(repo_id=repo_id, filepath=upload_filepath, mimetype=mimetype)
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
            rowCount = len(data)
            columnCount, columns, stats, recommendedSchema = AnalyzerManager.createAnalysis(repo_id, data, rowCount)
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
    def importData(repo_id, type, filename, original_filename, data_mapping, ignore_first, field_names, schema_name, data_types, field_descriptions, start=0):
        upload_filepath = os.path.join(UPLOAD_FOLDER, filename)
        mt = getMimetypeForFile(upload_filepath)
        data = UploadManager._generatePreview(filepath=upload_filepath, mimetype=mt, rows=1000000, start=start)
        print("UPLOADED FILE: " + str(len(data["data"])) + " rows")
        if data is None:
            raise ImportError(message="Could not read file", context="UploadManager.importData")

        if str(type) == "-1":
            # create type
            if schema_name:
                schema_type = re.sub(r'[^A-Za-z0-9_\-]+', '_', schema_name).lower()
            else:
                schema_name = 'new type'
                schema_type = 'new_type'

            # Check for exisiting type and iterate over _n suffixes until we find one that doesn't exist
            existing_type = SchemaManager.getInfoForType(repo_id, schema_type)
            if existing_type:
                i = 1
                while True:
                    schema_name = '_'+str(i)
                    schema_type = '_'+str(i)
                    existing_type = SchemaManager.getInfoForType(repo_id, schema_type)
                    if not existing_type:
                        break
                    i += 1
            new_type = SchemaManager.addType(repo_id, schema_name, schema_type, "Type created by import", {})
            print new_type
            if "type" in new_type:
                type = new_type["type"]["code"]

        SchemaManager.resetTypeInfoCache()
        type_info = SchemaManager.getInfoForType(repo_id, type)

        if type_info is None:
            raise ImportError(message="Invalid type", context="UploadManager.importData")
        typecode = type_info["code"]

        fields_created = {}
        # create new fields
        print data_mapping
        print field_names
        for i, m in enumerate(data_mapping):
            print m
            try:
                fid = int(m)
                field_info = SchemaManager.getInfoForField(repo_id, type, fid)
                if field_info is None:
                    data_mapping[i] = 0 # invalid field - don't import
                else:
                    data_mapping[i] = field_info["code"]
            except Exception as e:
                # is not id... does field with this code exist?
                if field_names[i] != data_mapping[i]:
                    m = field_names[i]
                mCode = re.sub(r'[^A-Za-z0-9_\-]+', '_', m).lower()
                data_mapping[i] = mCode
                field_info = SchemaManager.getInfoForField(repo_id, type, m)
                if field_info is None:
                    # create new field
                    mField = ''
                    if field_descriptions[i]:
                        mField = field_descriptions[i]
                    new_field = SchemaManager.addField(repo_id, type, m, mCode, data_types[i], mField,{})
                    if new_field is not None:
                        print new_field
                        data_mapping[i] = new_field["code"]
                        fields_created[typecode] = new_field
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
        num_errors = 0
        errors = {}
        counts = {}

        # TODO: record original file name, file size, file type
        upload_uuid = UploadManager.createImportEvent(repo_id, type_info["code"], upload_filepath, original_filename, data["type"], len(data["data"]))
        for line, r in enumerate(data["data"]):
            fields = {}
            print r
            for i, fid in enumerate(data_mapping):
                if fid not in fieldmap:
                    continue
                if isinstance(r, list):
                    fields[fid] = r[i]
                    continue
                if data["headers"][i] not in r:
                    continue
                fields[fid] = r[data["headers"][i]]
            try:
                DataManager.add(repo_id, type, fields, upload_uuid)
                if type not in counts:
                    counts[typecode] = 1
                else:
                    counts[typecode] = counts[typecode] + 1
            except Exception as e:
                if line not in errors:
                    errors[line] = []
                errors[line].append(e.message)
                num_errors = num_errors + 1

        UploadManager.closeImportEvent(upload_uuid)
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
        return r['uuid']

    @staticmethod
    def closeImportEvent(uuid):
        result = db.run(
            "MATCH (e:ImportEvent { uuid: {uuid}}) SET e.ended_on = {time} RETURN e.uuid as uuid",
            {"uuid": uuid, "time": time.time()})
        print result
        if result is None:
            return False
        r = result.peek()
        return r['uuid']

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
