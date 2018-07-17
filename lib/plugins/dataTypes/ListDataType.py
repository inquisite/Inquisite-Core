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

    priority = 70

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
        if len(value_array) > 1024:
            return False

        if len(set(value_array)) != len(value_array):
            # There are duplicates in the "list" so probably not a real list
            return False

        self.tmp_value = value_array

        return True

    #
    #
    #
    def parse(self, value, list_code, repo_id):
        if value != self.tmp_value:
            self.validate(value)

        list_info = ListManager.getInfoForList(repo_id, list_code)
        merge_allowed = list_info['merge_allowed']
        if not merge_allowed:
            merge_allowed = 0
        else:
            merge_allowed = int(merge_allowed)
        if merge_allowed == 0:
            check_items = []
            for item in list_info['items']:
                check_items.append(item['code'])
        items = []
        rejected = []

        if isinstance(self.tmp_value, list):
            for item in self.tmp_value:
                item_code = re.sub(r'[^A-Za-z0-9_]+', '_', item).lower()
                if merge_allowed == 0 and item_code not in check_items:
                    rejected.append(item_code)
                    continue
                list_item = ListManager.addListItem(repo_id, list_code, item, item_code)
                items.append(str(list_item["item_id"]))
        else:
            item_code = re.sub(r'[^A-Za-z0-9_]+', '_', self.tmp_value).lower()
            if merge_allowed == 0 and item_code not in check_items:
                rejected.append(item_code)
            else:
                list_item = ListManager.addListItem(repo_id, list_code, self.tmp_value, item_code)
                items.append(list_item["id"])

        d = self.parsed_value = {"list_items": ', '.join(items), "rejected_items": rejected}
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
    #
    #
    def getTmpValue(self):
        return self.tmp_value

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
