import json
from lib.plugins.dataReaders.BaseDataReader import BaseDataReader
from lib.exceptions.FileError import FileError

class JSONDataReader(BaseDataReader):
  name = "JSON Data Reader"
  description = "Reads JSON formatted data"
  type = "JSON"

  priority = 30

  def __init__(self, filepath=None):
    super(JSONDataReader, self).__init__(filepath)

  #
  @classmethod
  def identify(cls, filepath):
    try:
        json.load(open(filepath, "r"))
        return True
    except:
        pass
    return False

  #
  def read(self, filepath):
    self.input_file = None

    try:
      self.input_file = open(filepath, 'rb')
    except:
      pass

    super(JSONDataReader, self).read(filepath)

    if self.input_file:
      return True
    else:
      return False

  # TODO: support start parameter
  def getRows(self, rows=None, start=0):
    if self.input_file is None:
        raise FileError("No file loaded", "JSONDataReader.getRows")

    file_data = []

    # TODO: support start/rows?
    with self.input_file as jsonfile:
      file_data = json.load(jsonfile)

    return file_data

