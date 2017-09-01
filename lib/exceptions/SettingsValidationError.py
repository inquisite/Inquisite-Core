class SettingsValidationError(Exception):
    def __init__(self, message, errors, context=''):
        self.message = message
        self.errors = errors
        self.context = context