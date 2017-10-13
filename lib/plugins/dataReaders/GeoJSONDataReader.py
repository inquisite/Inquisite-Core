import json
from lib.plugins.dataReaders.BaseDataReader import BaseDataReader
from lib.exceptions.FileError import FileError

class GeoJSONDataReader(BaseDataReader):
  name = "GeoJSON Data Reader"
  description = "Reads GeoJSON formatted data"

  priority = 20

  def __init__(self, filepath=None):
    super(GeoJSONDataReader, self).__init__(filepath)

  #
  @classmethod
  def identify(cls, filepath):
    try:
        json.load(open(filepath, "r"))
        return True
    except Exception as e:
        print e.message
        pass
    return False

  #
  def read(self, filepath):
    self.input_file = None

    try:
      self.input_file = open(filepath, 'rb')
    except:
      pass

    super(GeoJSONDataReader, self).read(filepath)

    if self.input_file:
      return True
    else:
      return False

  def getRows(self, rows=None, start=0):
    if self.input_file is None:
      raise FileError("No file loaded", "GeoJSONDataReader.getRows")
    file_data = []

    # TODO: support start/rows?
    with self.input_file as jsonfile:
      file_data = json.load(jsonfile)

    return file_data
