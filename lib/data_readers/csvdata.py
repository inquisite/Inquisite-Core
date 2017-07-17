import csv
import json

class CsvHandler():

  input_file = None

  def __init__(self, input_file):
    self.input_file = input_file

  def read_file(self):

    file_data = []
    with open(self.input_file, 'rb') as csvfile:
      for row in csv.DictReader( csvfile ):
        file_data.append(json.dumps(row))

    return file_data

