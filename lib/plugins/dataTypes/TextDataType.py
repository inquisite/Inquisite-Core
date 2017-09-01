from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class TextDataType(BaseDataType):
    name = "Text"
    description = "Text value"

    settings_spec = {
        "order": ["min_length", "max_length"],
        "settings": {
            "min_length": {
                "type": "integer",
                "label": "Minimum length",
                "description": "Minimum number of characters allowed in text input.",
                "min": 0,
                "default": 0,
                "render": "field",
                "width": "200px"
            },
            "max_length": {
                "type": "integer",
                "label": "Maximum length",
                "description": "Maximum number of characters allowed in text input.",
                "min": 0,
                "default": 65535,
                "render": "field",
                "width": "200px"
            }
        }
    }

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(TextDataType, self).__init__(value)

    #
    # Validate value
    #
    def validate(self, settings, *args):
        pass

    #
    # Validate settings values
    #
    def validateSettings(self, settingsValues):
        errs = super(TextDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if (int(settingsValues['min_length']) > int(settingsValues['max_length'])):
            errs.append("Minimum length must be less than maximum length")

        if len(errs) > 0:
            return errs
        return True


