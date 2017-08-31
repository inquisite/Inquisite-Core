from lib.plugins.BasePlugin import BasePlugin
from lib.utils import Settings

class BaseDataType(BasePlugin):
    val = None

    #
    #
    #
    def __init__(self, value=None):
        if value is not None:
            self.set(value)
        super(BaseDataType, self).__init__()

    #
    # Set value
    #
    def set(self, value):
        self.val = value

    #
    # Get value
    #
    def get(self):
        return self.val

    #
    # Validate a value for the data type subject to settings. Should be overridden by data type sub-class.
    #
    def validate(self, settings, value=None):
        return True

    #
    # Get settings specifications for data type. This is a dictionary with settings codes, descriptions,
    # validation rules and rendering suggestions
    #
    @classmethod
    def getSettingsList(cls):
        return cls.settings.getSettings()

    #
    # Get settings instance
    #
    @classmethod
    def getSettingsInstance(cls):
        return cls.settings