from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class GeorefDataType(BaseDataType):
    name = "Georeference"
    description = "Georeference value"

    settings_spec = {
        "order": ["min_length", "max_length"],
        "settings": {
            # "min_length": {
            #     "type": "integer",
            #     "label": "Minimum length",
            #     "description": "Minimum number of characters allowed in text input.",
            #     "min": 0,
            #     "default": 0,
            #     "render": "field",
            #     "width": "200px"
            # },
            # "max_length": {
            #     "type": "integer",
            #     "label": "Maximum length",
            #     "description": "Maximum number of characters allowed in text input.",
            #     "min": 0,
            #     "default": 65535,
            #     "render": "field",
            #     "width": "200px"
            # }
        }
    }

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(TextDataType, self).__init__(value)

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):
        # min_length = self.settings.getValue("min_length")
        # max_length = self.settings.getValue("max_length")
        # l = len(value)

        errors = []

        # if (l < min_length):
        #     errors.append("Value must be longer than " + str(min_length) + " characters")
        # if (l > max_length):
        #     errors.append("Value must be shorter than " + str(max_length) + " characters")

        if (len(errors) > 0):
            return errors
        return True

    #
    # Georeference-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(GeorefDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        #if (int(settingsValues.get('min_length', self.settings.getValue("min_length"))) > int(settingsValues.get('max_length', self.settings.getValue("max_length")))):
        #    errs.append("Minimum length must be less than maximum length")

        if len(errs) > 0:
            return errs
        return True


