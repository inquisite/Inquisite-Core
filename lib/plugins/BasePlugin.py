class BasePlugin(object):
    def __init__(self):
        pass

    #
    # Return name of plugin (all plugins set self.name)
    #
    def getPluginName(self):
        return self.name
