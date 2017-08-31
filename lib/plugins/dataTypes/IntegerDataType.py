from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class IntegerDataType(BaseDataType):
    settings_spec = {
        "min_value": {
            "type": "integer",
            "label": "Minimum value",
            "description": "Minimum value allowed.",
            "min": 0,
            "default": 0,
            "render": "field"
        },
        "max_value": {
            "type": "integer",
            "label": "Maximum value",
            "description": "Maximum value allowed.",
            "min": 0,
            "default": None,
            "render": "field"
        }
    }

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        self.name = "Integer"
        super(IntegerDataType, self).__init__(value)