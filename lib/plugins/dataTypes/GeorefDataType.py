from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings
import json
import numbers
import re

class GeorefDataType(BaseDataType):
    name = "Georeference"
    description = "Georeference value"

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

    priority = 10

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(GeorefDataType, self).__init__(value)

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):
        # min_length = self.settings.getValue("min_length")
        # max_length = self.settings.getValue("max_length")
        # l = len(value)

        errors = []

        self.parsed_value = None


        geotype = None

        # Is it a GeoJSON geometry object as text?
        json_data = None
        if isinstance(value, basestring):
            str_coords = re.search(r'^(?:\(|\[|\{)([\d\.-]+)(?:, |,)([\d\.-]+)(?:\)|\]|\})$', value)
            if str_coords:
                json_data = {"type": "point", "coordinates": [float(str_coords.group(2)), float(str_coords.group(1))]}
                print json_data
            else:
                try:
                    json_data = json.loads(value.lower())
                    if ("coordinates" not in json_data) or ("type" not in json_data) \
                            or (json_data["type"] not in ["point", "polygon"]) \
                            or ((len(json_data["coordinates"]) == 0) or (GeorefDataType.isCoordinateList(json_data["coordinates"], json_data["type"]) is False)):
                        return False
                except Exception as e:
                    errors.append("Could not parse %(value)s into geoJSON object" % {"value": value})
                    pass

        # Is it a GeoJSON geometry object
        if isinstance(value, dict):
            value = {k.lower(): v for k, v in value.items()}
            try:
                if ("coordinates" in value) and ("type" in value) and (value["type"].lower() in ["point", "polygon"]) \
                        and ((len(value["coordinates"]) > 0) and GeorefDataType.isCoordinateList(value["coordinates"], value["type"].lower())):
                    json_data = value
                else:
                    return False
            except Exception as e:
                errors.append("Could not parse %(value)s into geoJSON object" % {"value": value})
        if json_data is None:
            return False
        #print json.dumps(json_data, indent=4, sort_keys=True)

        # Is the value a single coordinate?

        # Is it a list of coordinates?

        # Is the value an array of coordinates (a single path)?

        # Is the value a series of paths?

        # Is the value a text address? If so try to geolocate it

        # Normalize to array of arrays

        # if (l < min_length):
        #     errors.append("Value must be longer than " + str(min_length) + " characters")
        # if (l > max_length):
        #     errors.append("Value must be shorter than " + str(max_length) + " characters")

        self.parsed_value = json_data
        if (len(errors) > 0):
            return errors
        return True

    #
    #
    #
    def parse(self, value):

        if self.validate(value) is False:
            return False

        if self.parsed_value is not None:
            return json.dumps(self.parsed_value)
        return False

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

    #
    # Utilities
    #
    @classmethod
    def isCoordinateList(cls, l, geoType):
        if geoType == 'polygon':
            l = l[0]
            if (type(l) is list) and (len(l) > 0):
                coords = [v for v in l if ((type(v) is list) or (type(v) is tuple)) and ((len(v) == 2) or (len(v) == 3))
                     and isinstance(v[0], numbers.Number) and isinstance(v[1], numbers.Number)]
        else:
            if(type(l) is list) and (len(l) == 2):
                coords = [v for v in l if isinstance(v, numbers.Number)]

        if len(coords) > 0:
            return True

        return False
