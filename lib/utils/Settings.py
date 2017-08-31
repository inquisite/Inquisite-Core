class Settings:

    settings = {}

    def __init__(self, settings):
        self.setSettings(settings)

    def setSettings(self, settings):
        # TODO: validate spec
        self.settings = settings
        return True

    def getSettings(self):
        return self.settings

    def validateSetting(self, setting, value):
        # TODO: perform validation
        return True