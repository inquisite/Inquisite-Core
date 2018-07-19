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
      with self.input_file as jsonfile:
        self.input_data = json.load(self.input_file)
    except:
      pass

    super(JSONDataReader, self).read(filepath)

    if self.input_file:
      self.headers = self.getHeaders()
      return True
    else:
      return False

  #
  def getHeaders(self):
    file_data = self.input_data
    # TODO Support JSON files as dicts, not sure how that would work though
    headers = []
    if isinstance(file_data, dict):
        pass
    elif isinstance(file_data, list):
        for row in file_data:
            if isinstance(row, dict):
                new_heads = row.keys()
                headers = list(set(headers + new_heads))
            else:
                # TODO Handle other types?
                pass

    return headers


  # TODO: support start parameter
  def getRows(self, rows=None, start=0):
    if self.input_file is None:
        raise FileError("No file loaded", "JSONDataReader.getRows")

    file_data = []

    # TODO: support start/rows?
    file_data = self.input_data
    print file_data

    return file_data
