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