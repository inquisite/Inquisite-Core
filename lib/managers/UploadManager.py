import os
import os.path
import hashlib, glob

from flask import Blueprint, request
from lib.exceptions.UploadError import UploadError
from lib.utils.FileHelpers import getMimetypeForFile


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
        print request.files
        if 'data_file' not in request.files:
            raise UploadError(message="File not found", context="UploadManager.processUpload()")

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
                                  context="UploadManager.processUpload()")

            mimetype = getMimetypeForFile(upload_filepath)
            if mimetype is None:
                os.remove(upload_filepath)
                raise UploadError(message="Unrecognized file", context="UploadManager.processUpload()")

            if UploadManager.allowed_file(mimetype) is False:
                os.remove(upload_filepath)
                raise UploadError(message="File type " + mimetype + " is not allowed",
                                  context="UploadManager.processUpload()")

            return {
                "filesize": os.path.getsize(upload_filepath),
                "filename": filename,
                "original_filename": original_filename,
                "mimetype": mimetype
            }


        raise UploadError(message="No file uploaded", context="UploadManager.processUpload()")


    #
    # Generate preview data for file
    #
    @staticmethod
    def generatePreview():
        pass

    #
    #
    #
    @staticmethod
    def allowed_file(mimetype):
        return mimetype in ALLOWED_MIMETYPES