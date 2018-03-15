import re
from lib.managers.ListManager import ListManager
from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings

class ListDataType(BaseDataType):
    name = "List"
    description = "List of distinct values (e.g. tags or other repeating data)"

    settings_spec = {
        "order": ["list_code", "search_display", "min_length", "max_length"],
        "settings": {
            "min_length": {
                "type": "integer",
                "label": "Minimum length",
                "description": "Minimum length of distinct values for this to be a list.",
                "min": 2,
                "default": 2,
                "render": "list",
                "width": "200px"
            },
            "max_length": {
                "type": "integer",
                "label": "Maximum length",
                "description": "Maximum length of list accepted by the system.",
                "min": 1024,
                "default": 1024,
                "render": "list",
                "width": "200px"
            },
            "search_display": {
               "type": "boolean",
               "label": "Search display",
               "description": "Toggle to set if this field should be displayed in search results.",
               "render": "select",
            },
            "list_code": {
                "type": "text",
                "label": "List Code",
                "description": "Internal List Code that sets controlled list of terms available for this field",
                "render": "select",
                "source": "list"
            }
        }
    }

    priority = 60

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(ListDataType, self).__init__(value)
        self.parsed_value = None
        self.tmp_value = None

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):

        if not isinstance(value, basestring):
            return False

        split_regex = r'[,;|\/]{1}'
        value_array = re.split(split_regex, value)
        #print value_array
        if len(value_array) < 2 or len(value_array) > 1024:
            #print "Array length out of range"
            return False

        if len(set(value_array)) != len(value_array):
            # There are duplicates in the "list" so probably not a real list
            #print "Duplicates invalidate the list"
            return False

        for term in value_array:
            if len(term) > 20:
                #print "A term is too long"
                return False

        self.tmp_value = value_array

        return True

    #
    #
    #
    def parse(self, value, list_code, repo_id):
        if value != self.tmp_value: # avoid reparsing dates already processed by validation
            self.validate(value)

        items = []
        print list_code, repo_id
        print self.tmp_value
        if isinstance(self.tmp_value, list):
            for item in self.tmp_value:
                item_code = re.sub(r'[^A-Za-z0-9_]+', '_', item).lower()
                list_item = ListManager.addListItem(repo_id, list_code, item, item_code)
                print list_item
                items.append(str(list_item["item_id"]))
        else:
            item_code = re.sub(r'[^A-Za-z0-9_]+', '_', self.tmp_value).lower()
            list_item = ListManager.addListItem(repo_id, list_code, self.tmp_value, item_code)
            items.append(list_item["id"])

        d = self.parsed_value = {"list_items": ', '.join(items)}
        if d is not None:
            return d
        return False

    #
    #
    #
    def set(self, value):
        if self.validate(value) is False:
            return False
        self.val = value

    #
    #
    #
    def getParsedValue(self):
        return self.parsed_value



    #
    # Float-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(ListDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        if len(errs) > 0:
            return errs
        return True
