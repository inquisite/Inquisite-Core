import csv
from lib.plugins.dataReaders.BaseDataReader import BaseDataReader
from lib.exceptions.FileError import FileError

class TabDataReader(BaseDataReader):
  name = "Tab Data Reader"
  description = "Reads tab-delimited data"

  priority = 40

  def __init__(self, filepath=None):
    super(TabDataReader, self).__init__(filepath)

  #
  @classmethod
  def identify(cls, filepath):
    try:
      input_file = open(filepath, 'rb')
      dialect = csv.Sniffer().sniff(input_file.read(1024),"\t")
      input_file.close()
      if dialect.delimiter == "\t":
        return True
    except Exception as e:
      pass
    return False

  #
  def read(self, filepath):
    self.input_file = None

    try:
      self.input_file = open(filepath, 'rb')
    except:
      pass

    super(TabDataReader, self).read(filepath)

    if self.input_file:
      return True
    else:
      return False

  def getRows(self, rows=None, start=0):
    if self.input_file is None:
      raise FileError("No file loaded", "TabDataReader.getRows")

    file_data = []
    with self.input_file as line:

      c = 0
      for row in csv.DictReader(line, delimiter='\t'):
        c = c + 1
        if start is not None and c < start:
          continue
        if rows is not None and c > rows:
          break
        file_data.append(row)

    return file_data

