from lib.plugins.dataTypes.BaseDataType import BaseDataType

class Text(BaseDataType):
    def __init__(self, value=None):
        self.name = "Text"

        if value is not None:
            self.text = value


        super(Text, self).__init__()

    def getValue(self):
        return self.text

    def validate(self):
        return True
