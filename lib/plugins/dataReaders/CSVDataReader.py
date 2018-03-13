import csv
import re
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
        dialect = csv.Sniffer().sniff(input_file.readline(), ",")
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
            self.input_file = open(filepath, 'rU')
        except:
            return False

        if csv.Sniffer().has_header(self.input_file.readline()):
          self.input_file.seek(0)
          hr = self.headers = csv.reader(self.input_file)
          for h in hr:
            self.headers = h
            break
          self.input_file.seek(0)
        for pos, head in enumerate(self.headers):
            if isinstance(head, str):
                self.headers[pos] = unicode(head, errors="ignore").replace(u'\ufeff', '')
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
                print row
                row = dict(map(lambda x: ((unicode(x[0], errors="ignore"), unicode(x[1], errors="ignore")) if isinstance(x[1], str) else (unicode(x[0], errors="ignore"), x[1])), row.iteritems()))
                print row
                file_data.append(row)

        return file_data
