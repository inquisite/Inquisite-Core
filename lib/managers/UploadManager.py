import os
import os.path
import hashlib, glob
import re

from flask import Blueprint, request
from lib.exceptions.UploadError import UploadError
from lib.exceptions.ImportError import ImportError
from lib.utils.FileHelpers import getMimetypeForFile
from lib.dataReaders.XLSData import XLSReader
from lib.dataReaders.CSVData import CSVReader
from lib.managers.DataManager import DataManager
from lib.managers.SchemaManager import SchemaManager


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
    def _generatePreview(filepath, mimetype, rows=10):
        data = []
        headers = []
        if mimetype in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            preview_type = "table"

            data = XLSReader.getRows(filepath=filepath, rows=11)
            if data is None or len(data) == 0:
                return []
            headers = data[0]

            if len(filter(lambda x: re.match(r'^[\d]$', x), headers)) > 0 or len(set(headers)) < len(headers):
                # no headers
                headers = range(1, len(headers))
            else:
                # TODO: looks like valid headers... maybe clean them up somehow?
                pass

        elif mimetype == "text/plain":
            preview_type = "table"
            # TODO: distinguish between CSV and TAB

            data_dict = CSVReader.getRows(filepath=filepath, rows=11)
            if data_dict is None or len(data_dict) == 0:
                return []
            headers = data_dict[0].keys()

            data = map(lambda x: x.values(), data_dict)
        elif mimetype == "text/json":
            preview_type = "json"
            pass
        else:
            raise UploadError(message="Cannot extract preview data for unsupported file type " + mimetype, context="UploadManager._generatePreview")
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
    def importData(repo_id, type, filename, data_mapping):
        upload_filepath = os.path.join(UPLOAD_FOLDER, filename)
        data = UploadManager._generatePreview(filepath=upload_filepath, mimetype=getMimetypeForFile(upload_filepath), rows=None)
        if data is None:
            raise ImportError(message="Could not read file", context="UploadManager.importData")

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

        data_mapping = map(lambda x: str(x), data_mapping)

        num_errors = 0
        errors = {}
        counts = {}
        for line, r in enumerate(data["data"]):
            fields = {}
            for i, fid in enumerate(data_mapping):
                fields[fid] = r[i]
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