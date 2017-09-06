import csv
import json

class CSVReader():

  input_file = None

  #def __init__(self, input_file):
  #  self.input_file = input_file

  @classmethod
  def getRows(cls, filepath, rows=None, start=0):

    file_data = []
    with open(filepath, 'rb') as csvfile:

      c = 0
      for row in csv.DictReader( csvfile ):
        c = c + 1
        if start is not None and c < start:
          continue
        if rows is not None and c > rows:
          break
        file_data.append(row)

    return file_data

