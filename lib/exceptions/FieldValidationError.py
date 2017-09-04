class FieldValidationError(Exception):
    def __init__(self, message, type, field, errors, context='', value=None):
        self.message = message
        self.errors = errors
        self.type = type
        self.field = field
        self.context = context
        self.value = value