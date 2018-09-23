from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings
import json
import numbers
import re
import requests

class MediaDataType(BaseDataType):
    name = "Media"
    description = "Media value"

    settings_spec = {
        "order": ["search_display", "max_size"],
        "settings": {
            "max_size": {
                 "type": "integer",
                 "label": "Maximum size in bytes",
                 "description": "Maximum file size, in bytes",
                 "min": 0,
                 "default": 0,
                 "render": "field",
                 "width": "200px"
            },
             "search_display": {
                "type": "boolean",
                "label": "Search display",
                "description": "Toggle to set if this field should be displayed in search results.",
                "render": "select",
             }
        }
    }

    priority = 1211

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(MediaDataType, self).__init__(value)
        config = json.load(open('./config.json'));

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):
        errors = []

        self.parsed_value = None


        
        if (len(errors) > 0):
            return errors
        return True

    #
    #
    #
    def parse(self, value):

        if self.validate(value) is False:
            return False
        
        return "MEDIA"
        #return False
        
    #
    # Media-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(MediaDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        #if (int(settingsValues.get('min_length', self.settings.getValue("min_length"))) > int(settingsValues.get('max_length', self.settings.getValue("max_length")))):
        #    errs.append("Minimum length must be less than maximum length")

        if len(errs) > 0:
            return errs
        return True

    #
    # Utilities
    #
    @classmethod
    def getMedia(cls, l):
        return False
