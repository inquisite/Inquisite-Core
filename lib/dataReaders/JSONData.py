import json

class JSONReader():

  input_file = None

  #def __init__(self, input_file):
  #  self.input_file = input_file

  @classmethod
  def getRows(cls, filepath, rows=None, start=0):
    file_data = []

    # TODO: support start/rows?
    with open(self.input_file) as jsonfile:
      file_data = json.load(jsonfile)

    return file_data

