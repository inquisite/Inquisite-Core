class DbError(Exception):
    def __init__(self, message, context='', dberror=''):
        self.message = message
        self.context = context
        self.dberror = dberror