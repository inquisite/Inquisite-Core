from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class BooleanDataType(BaseDataType):
    name = "Boolean"
    description = "Boolean (True/False) Value"

    settings_spec = {
        "order": ["search_display", "min_value", "max_value"],
        "settings": {
            "min_value": {
                "type": "integer",
                "label": "Minimum value",
                "description": "Minimum value to be assigned for boolean.",
                "min": 0,
                "default": 0,
                "render": "list",
                "width": "100px"
            },
            "max_value": {
                "type": "integer",
                "label": "Maximum value",
                "description": "Maximum value to be assigned for boolean.",
                "min": 0,
                "default": 1,
                "render": "list",
                "width": "100px"
            },
            "search_display": {
               "type": "boolean",
               "label": "Search display",
               "description": "Toggle to set if this field should be displayed in search results.",
               "render": "select",
            }
        }
    }

    priority = 10

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(BooleanDataType, self).__init__(value)
        self.parsed_value = None

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):

        if isinstance(value, basestring):
            check_value = value.lower()
            if check_value in ['yes', 'true', 't', 'y']:
                self.parsed_value = {"boolean": 1}
                return True
            elif check_value in ['no', 'false', 'f', 'n']:
                self.parsed_value = {"boolean": 0}
                return True

        if isinstance(value, int):
            if value == 1 or value == 0:
                self.parsed_value = {"boolean": value}
                return True

        return False

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
        errs = super(BooleanDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if len(errs) > 0:
            return errs
        return True
