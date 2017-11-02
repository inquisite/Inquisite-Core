import os
import os.path
import hashlib, glob
import re

from flask import Blueprint, request
from lib.exceptions.UploadError import UploadError
from lib.exceptions.ImportError import ImportError
from lib.utils.FileHelpers import getMimetypeForFile
from lib.managers.DataManager import DataManager
from lib.managers.SchemaManager import SchemaManager
from lib.managers.DataReaderManager import DataReaderManager


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
            return {
                "filesize": os.path.getsize(upload_filepath),
                "filename": filename,
                "original_filename": original_filename,
                "mimetype": mimetype,
                "preview": preview
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
        return {"headers": headers, "data": data, "type": preview_type}

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
    def importData(repo_id, type, filename, data_mapping, start=0):
        upload_filepath = os.path.join(UPLOAD_FOLDER, filename)
        data = UploadManager._generatePreview(filepath=upload_filepath, mimetype=getMimetypeForFile(upload_filepath), rows=1000000, start=start)
        print("UPLOADED FILE: " + str(len(data["data"])) + " rows")
        if data is None:
            raise ImportError(message="Could not read file", context="UploadManager.importData")

        if str(type) == "-1":
            # create type
            # TODO: make sure "new type" name is unique
            new_type = SchemaManager.addType(repo_id, "New type", "new_type", "Type created by import", {})

            if "type" in new_type:
                type = new_type["type"]["code"]

        type_info = SchemaManager.getInfoForType(repo_id, type)
        if type_info is None:
            raise ImportError(message="Invalid type", context="UploadManager.importData")
        typecode = type_info["code"]

        fields_created = {}
        # create new fields
        for i, m in enumerate(data_mapping):
            try:
                fid = int(m)
                field_info = SchemaManager.getInfoForField(repo_id, type, fid)
                if field_info is None:
                    data_mapping[i] = 0 # invalid field - don't import
                else:
                    data_mapping[i] = field_info["code"]
            except Exception as e:
                # is not id... does field with this code exist?
                field_info = SchemaManager.getInfoForField(repo_id, type, m)
                if field_info is None:
                    # create new field
                    # TODO: support field types other than text
                    new_field = SchemaManager.addField(repo_id, type, m, m, 'TextDataType','',{})
                    if new_field is not None:
                        data_mapping[i] = new_field["code"]
                        fields_created[typecode] = new_field
                    else:
                        data_mapping[i] = 0
                else:
                    # set mapping to use field code
                    data_mapping[i] = field_info["code"]

        fieldmap = {}
        for v in type_info["fields"]:
            fieldmap[v["code"]] = v

        data_mapping = map(lambda x: str(x), data_mapping)

        num_errors = 0
        errors = {}
        counts = {}

        for line, r in enumerate(data["data"]):
            fields = {}
            for i, fid in enumerate(data_mapping):
                if fid not in fieldmap:
                    continue
                if data["headers"][i] not in r:
                    continue
                fields[fid] = r[data["headers"][i]]
            try:
                DataManager.add(repo_id, type, fields)
                if type not in counts:
                    counts[typecode] = 1
                else:
                    counts[typecode] = counts[typecode] + 1
            except Exception as e:
                if line not in errors:
                    errors[line] = []
                errors[line].append(e.message)
                num_errors = num_errors + 1

        return {"errors": errors, "error_count": num_errors, "mapping": data_mapping, "fields_created": fields_created, "counts": counts, "filename": filename}