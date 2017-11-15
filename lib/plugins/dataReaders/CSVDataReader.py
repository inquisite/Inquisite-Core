import csv
from lib.plugins.dataReaders.BaseDataReader import BaseDataReader
from lib.exceptions.FileError import FileError


class CSVDataReader(BaseDataReader):
    name = "CSV Data Reader"
    description = "Reads Comma-delimited data"
    type = "CSV text"

    priority = 50

    def __init__(self, filepath=None):
        super(CSVDataReader, self).__init__(filepath)

    #
    @classmethod
    def identify(cls, filepath):
      try:
        input_file = open(filepath, 'rb')
        dialect = csv.Sniffer().sniff(input_file.read(1024), ",")
        input_file.close()
        if dialect.delimiter == ',':
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
            return False

        if csv.Sniffer().has_header(self.input_file.read(8192)):
          self.input_file.seek(0)
          hr = self.headers = csv.reader(self.input_file)
          for h in hr:
            self.headers = h
            break
          self.input_file.seek(0)

        super(CSVDataReader, self).read(filepath)


        if self.input_file:
            return True
        else:
            return False

    def getRows(self, rows=None, start=0):
        if self.input_file is None:
          raise FileError("No file loaded", "CSVDataReader.getRows")

        file_data = []
        with self.input_file as line:
            c = 0
            for row in csv.DictReader(line):
                c = c + 1
                if start is not None and c < start:
                    continue
                if rows is not None and c > rows:
                    break
                file_data.append(row)

        return file_data
