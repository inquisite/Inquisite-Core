from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class IntegerDataType(BaseDataType):
    name = "Integer"
    description = "Integer (whole) numeric value"

    settings_spec = {
        "order": ["min_value", "max_value"],
        "settings": {
            "min_value": {
                "type": "integer",
                "label": "Minimum value",
                "description": "Minimum value allowed.",
                "min": 0,
                "default": 0,
                "render": "field",
                "width": "100px"
            },
            "max_value": {
                "type": "integer",
                "label": "Maximum value",
                "description": "Maximum value allowed.",
                "min": 0,
                "default": None,
                "render": "field",
                "width": "100px"
            }
        }
    }

    priority = 10

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(IntegerDataType, self).__init__(value)

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):
        try:
            integer = int(value)
        except ValueError:
            return False

        return True


    #
    # Integer-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(IntegerDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if (int(settingsValues['min_value']) > int(settingsValues['max_value'])):
            errs.append("Minimum value must be less than maximum value")

        if len(errs) > 0:
            return errs
        return True
