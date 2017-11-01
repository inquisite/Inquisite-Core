import re
from pluginbase import PluginBase
from lib.decorators.Memoize import memoized

class DataReaderManager:
    plugin_source = PluginBase(package='lib.plugins.dataReaders').make_plugin_source(
        searchpath=['lib/plugins/dataReaders'], identifier='inquisiteDataReaders')

    dataReaderPlugins = {}
    dataReaderPluginsByPriority = []
    pluginsAreLoaded = False

    def __init__(self):
        pass

    #
    #
    #
    @classmethod
    def identify(cls, filepath):
        for n in DataReaderManager.getDataReaders():
            #print "TRY " + n
            i = DataReaderManager.getDataReaderInstance(n)
            if i is None:
                continue
            if i.identify(filepath):
                return i
        return None

    #
    #
    #
    @classmethod
    def loadDataReaderPlugins(cls):
        byPriority = {}
        for n in cls.plugin_source.list_plugins():
            if re.match("Base", n):
                continue
            c = getattr(cls.plugin_source.load_plugin(n), n)
            cls.dataReaderPlugins[n] = c
            byPriority[c.priority] = n

        for x in sorted(byPriority.iteritems()):
            cls.dataReaderPluginsByPriority.append(x[1])
        cls.pluginsAreLoaded = True
        return True

    #
    #
    #
    @classmethod
    @memoized
    def getDataReaders(cls):
        if cls.pluginsAreLoaded is False:
            cls.loadDataReaderPlugins()
        return cls.dataReaderPluginsByPriority

    #
    #
    #
    @classmethod
    @memoized
    def getInfoForDataReaders(cls):
        if cls.pluginsAreLoaded is False:
            cls.loadDataReaderPlugins()
        types = {}
        for x in DataReaderManager.getDataReaders():
            p = DataReaderManager.getDataReaderPlugin(x)
            types[x] = { "name": p.name, "description": p.description }
        return types

    #
    # Return plugin class
    #
    @classmethod
    @memoized
    def getDataReaderPlugin(cls, n):
        if cls.pluginsAreLoaded is False:
            cls.loadDataReaderPlugins()
        if n in cls.dataReaderPlugins:
            return cls.dataReaderPlugins[n]
        return None

    #
    # Returns plugin instance
    #
    @classmethod
    @memoized
    def getDataReaderInstance(cls, n):
        if cls.pluginsAreLoaded is False:
           cls.loadDataReaderPlugins()
        if n in cls.dataReaderPlugins:
            return cls.dataReaderPlugins[n]()
        return None