class ImportError(Exception):
    def __init__(self, message, context=''):
        self.message = message
        self.context = context