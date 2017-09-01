class Settings:

    settings = {}

    #
    #
    #
    def __init__(self, settings):
        self.setSettings(settings)

    #
    #
    #
    def setSettings(self, settings):
        # TODO: validate spec

        # Add "code" attribute by copying key
        for k, v in settings['settings'].iteritems():
            settings['settings'][k]['code'] = k
        self.settings = settings
        return True

    #
    #
    #
    def getSettings(self):
        return self.settings["settings"]

    #
    #
    #
    def getSettingsOrder(self):
        return self.settings["order"]

    #
    #
    #
    def getSetting(self, setting):
        pass

    #
    #
    #
    def validateSetting(self, setting, value):
        # TODO: perform validation
        return True

    #
    #
    #
    def xxx(self):
        pass