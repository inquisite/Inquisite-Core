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
        "order": ["search_display", "min_date", "max_date"],
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
            },
            "search_display": {
               "type": "boolean",
               "label": "Search display",
               "description": "Toggle to set if this field should be displayed in search results.",
               "render": "select",
            }
        }
    }

    priority = 50

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
        if re.match(r'[\d]+(?:/|\.|-|_)[\d]+(?:/|\.|-|_)[\d]+', value):
            date_components = re.findall(r'[\d]+', value)
            if len(date_components[2]) == 4:
                value = date_components[0] + "-" + date_components[1] + "-" + date_components[2]
            elif len(date_components[0]) == 4:
                value = date_components[1] + "-" + date_components[2] + "-" + date_components[0]
        #value = re.sub(r'([\d]+)/([\d]+)/([\d]+)', r"\3-\1-\2", unicode(value))
        return value



    #
    #
    #
    def validate(self, value):
        if(isinstance(value, basestring) is False):
            return False

        if re.match(r'[\d]+(?:-|_|\.|\/)[\d]+(?:-|_|\.|\/)[\d]+', value):
            range_match = re.findall(r'([\d]+(?:-|_|\.|\/)[\d]+(?:-|_|\.|\/)[\d]+)', value)
            if len(range_match) == 1:
                self.parsed_date = {"start": range_match[0], "end": range_match[0]}
            else:
                self.parsed_date = {"start": range_match[0], "end": range_match[1]}
            print self.parsed_date
            return True
        elif re.match(r'([\d]+)(?:-|_|\.|\/)([\d])', value):
            range_match = re.findall(r'([\d]+(?:-|_|\.|\/)[\d])', value)
        elif re.match(r'[a-zA-Z\.]+ [\d,]+ [\d]+', value):
            range_match = re.findall(r'([a-zA-Z\.]+ [\d,]+ [\d]+)', value)
        elif re.match(r'[\d]+ [a-zA-Z\.]+ [\d]+', value):
            range_match = re.findall(r'([\d]+ [a-zA-Z\.]+ [\d]+)', value)
        else:
            return False
        d = None
        if len(range_match) == 1:
            try:
                dx = dateutil.parser.parse(value)
            except ValueError:
                return False
            self.parsed_date = {"start": str(dx), "end": str(dx)}
        else:
            try:
                d = parse(value, allow_implicit=True)
            except ParseException as e:
                return False
            if d is None:
                #return ["Invalid date"]
                return False
            self.parsed_date = {"start": str(d[0]), "end": str(d[1])}

        self.value_parsed = value
        print self.parsed_date
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
