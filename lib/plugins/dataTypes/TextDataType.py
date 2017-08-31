from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class Text(BaseDataType):
    settings_spec = {
        "min_length": {
            "type": "integer",
            "label": "Minimum length",
            "description": "Minimum number of characters allowed in text input.",
            "min": 0,
            "default": 0,
            "render": "field"
        },
        "max_length": {
            "type": "integer",
            "label": "Maximum length",
            "description": "Maximum number of characters allowed in text input.",
            "min": 0,
            "default": 65535,
            "render": "field"
        }
    }

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        print "INIT TEXT"
        self.name = "Text"
        super(Text, self, value).__init__(value)
    def setup(self):
        print "SET UP" + self.name