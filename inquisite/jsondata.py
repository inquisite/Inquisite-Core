import json

class JSONHandler():

  input_file = None

  def __init__(self, input_file):
    self.input_file = input_file

  def read_file(self):

    file_data = []
    with open(self.input_file) as jsonfile:
      file_data = json.load(jsonfile)

    return file_data

