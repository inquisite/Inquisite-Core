from lib.plugins.BasePlugin import BasePlugin

class BaseDataReader(BasePlugin):
    #
    # Path to file being read
    #
    filepath = None

    #
    # File being read
    #
    input_file = None

    #
    #
    #
    headers = []

    #
    #
    #
    def __init__(self, filepath=None):
        super(BaseDataReader, self).__init__()
        if filepath:
            self.read(filepath)

    #
    #
    #
    def read(self, filepath):
        self.filepath = None
        if self.input_file:
            self.filepath = filepath
        return self.filepath

    def getHeaders(self):
        return self.headers

    #
    # Should be overridden. Returns true if file can be read by plugin.
    #
    @classmethod
    def identify(cls, filepath):
        return False