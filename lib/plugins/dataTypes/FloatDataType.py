from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class FloatDataType(BaseDataType):
    name = "Float"
    description = "Floating point (decimal) numeric value"

    settings_spec = {
        "order": ["min_value", "max_value"],
        "settings": {
            "min_value": {
                "type": "float",
                "label": "Minimum value",
                "description": "Minimum value allowed.",
                "min": 0,
                "default": 0,
                "render": "field",
                "width": "100px"
            },
            "max_value": {
                "type": "float",
                "label": "Maximum value",
                "description": "Maximum value allowed.",
                "min": 0,
                "default": None,
                "render": "field",
                "width": "100px"
            }
        }
    }

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(FloatDataType, self).__init__(value)


    #
    # Float-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(FloatDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if (float(settingsValues['min_value']) > float(settingsValues['max_value'])):
            errs.append("Minimum value must be less than maximum value")

        if len(errs) > 0:
            return errs
        return True