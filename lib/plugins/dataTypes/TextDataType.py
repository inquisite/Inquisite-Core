from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class TextDataType(BaseDataType):
    name = "Text"
    description = "Text value"

    settings_spec = {
        "order": ["search_display", "min_length", "max_length"],
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
            },
            "search_display": {
               "type": "boolean",
               "label": "Search display",
               "description": "Toggle to set if this field should be displayed in search results.",
               "render": "select",
            }
        }
    }

    priority = 60

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(TextDataType, self).__init__(value)

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):
        min_length = self.settings.getValue("min_length")
        max_length = self.settings.getValue("max_length")

        try:
            floater = float(value)
            return False
        except ValueError:
            pass
        except TypeError:
            pass

        try:
            l = len(unicode(value, errors='replace'))
        except:
            l = len(value)

        errors = []

        if (l < min_length):
            errors.append("Value must be longer than " + str(min_length) + " characters")
        if (l > max_length):
            errors.append("Value must be shorter than " + str(max_length) + " characters")

        if (len(errors) > 0):
            return errors

        return True

    #
    # Text-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(TextDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if ('min_length' in settingsValues) and ('max_length' in settingsValues) and (int(settingsValues.get('min_length', self.settings.getValue("min_length"))) > int(settingsValues.get('max_length', self.settings.getValue("max_length")))):
            errs.append("Minimum length must be less than maximum length")

        if len(errs) > 0:
            return errs
        return True
