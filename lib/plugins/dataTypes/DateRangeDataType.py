import re
from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings
import dateutil.parser
from daterangeparser import parse
from pyparsing import ParseException

class DateRangeDataType(BaseDataType):
    name = "Date range"
    description = "Date range value"

    settings_spec = {
        "order": ["min_date", "max_date"],
        "settings": {
            "min_date": {
                "type": "text",
                "label": "Minimum date",
                "description": "Minimum date allowed.",
                "min": 1,
                "default": "",
                "render": "field",
                "width": "100px"
            },
            "max_date": {
                "type": "text",
                "label": "Maximum date",
                "description": "Maximum date allowed.",
                "min": 1,
                "default": "",
                "render": "field",
                "width": "100px"
            }
        }
    }

    priority = 40

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(DateRangeDataType, self).__init__(value)
        self.parsed_date = None
        self.value_parsed = None

    #
    #
    #
    @staticmethod
    def _preprocess(value):
        value = re.sub(r'([\d]+)/([\d]+)/([\d]+)', r"\3-\1-\2", unicode(value))
        return value


    #
    #
    #
    def validate(self, value):
        value = DateRangeDataType._preprocess(value)
        d = None
        try:
            d = parse(value, allow_implicit=True)
        except ParseException as e:
            # fall back to dateutil parser
            try:
                dx = dateutil.parser.parse(value)
                if dx is not None:
                    d = [dx, None]
            except ValueError:
                d = None
        if d is None:
            #return ["Invalid date"]
            return False
        self.parsed_date = {"start": str(d[0]), "end": str(d[1])}
        if d[1] is None:
            self.parsed_date["end"] = self.parsed_date["start"]
        self.value_parsed = value
        return True

    #
    #
    #
    def parse(self, value):
        if value == self.value_parsed and self.parsed_date is not None: # avoid reparsing dates already processed by validation
            return self.parsed_date

        self.validate(value)
        d = self.getParsedValue()

        if d is not None:
            return d
        return False

    #
    #
    #
    def getParsedValue(self):
        return self.parsed_date

    #
    # Float-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(DateRangeDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        #if (float(settingsValues['min_value']) > float(settingsValues['max_value'])):
        #    errs.append("Minimum date must be less than maximum value")

        if len(errs) > 0:
            return errs
        return True
