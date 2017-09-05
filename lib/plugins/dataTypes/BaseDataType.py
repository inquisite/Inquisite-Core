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
        if self.parse(value) is False:
            return False
        self.val = value

    #
    # Get value
    #
    def get(self):
        return self.val

    #
    # Validate a value for the data type subject to settings. Should be overridden by data type sub-class.
    #
    def validate(self, value):
        return True

    #
    #
    #
    def parse(self, value):
        return self.val

    #
    #
    #
    def getParsedValue(self):
        return self.val

    #
    # Get settings specifications for data type. This is a dictionary with settings codes, descriptions,
    # validation rules and rendering suggestions
    #
    @classmethod
    def getSettingsList(cls):
        return cls.settings.getSettings()

    #
    # Get order of settings for display.
    #
    @classmethod
    def getSettingsOrder(cls):
        return cls.settings.getSettingsOrder()

    #
    # Get settings instance
    #
    @classmethod
    def getSettingsInstance(cls):
        return cls.settings

    #
    # Validate settings values
    #
    def validateSettings(self, settingsValues):
        return self.settings.validate(settingsValues)


    #
    # Set settings values
    #
    def setSettings(self, settingsValues):
        return self.settings.setValues(settingsValues)