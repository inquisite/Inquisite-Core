import re

from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class ListDataType(BaseDataType):
    name = "List"
    description = "List of distinct values (e.g. tags or other repeating data)"

    settings_spec = {
        "order": ["min_length", "max_length"],
        "settings": {
            "min_length": {
                "type": "integer",
                "label": "Minimum length",
                "description": "Minimum length of distinct values for this to be a list.",
                "min": 2,
                "default": 2,
                "render": "list",
                "width": "200px"
            },
            "max_length": {
                "type": "integer",
                "label": "Maximum length",
                "description": "Maximum length of list accepted by the system.",
                "min": 1024,
                "default": 1024,
                "render": "list",
                "width": "200px"
            }
        }
    }

    priority = 60

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(ListDataType, self).__init__(value)
        self.parsed_value = None

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):

        if not isinstance(value, basestring):
            return False

        split_regex = r'[,;|\/]{1}'
        value_array = re.split(split_regex, value)
        print value_array
        if len(value_array) < 2 or len(value_array) > 1024:
            print "Array length out of range"
            return False

        if len(set(value_array)) != len(value_array):
            # There are duplicates in the "list" so probably not a real list
            print "Duplicates invalidate the list"
            return False

        for term in value_array:
            if len(term) > 20:
                print "A term is too long"
                return False

        self.parsed_value = ', '.join(value_array)

        return True

    #
    #
    #
    def parse(self, value):
        if value == self.parsed_value: # avoid reparsing dates already processed by validation
            return self.parsed_value

        self.validate(value)
        d = self.getParsedValue()

        if d is not None:
            return d
        return False

    #
    #
    #
    def getParsedValue(self):
        return self.parsed_value

    #
    # Float-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(ListDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if len(errs) > 0:
            return errs
        return True
