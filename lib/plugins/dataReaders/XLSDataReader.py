import xlrd
from lib.plugins.dataReaders.BaseDataReader import BaseDataReader
from lib.exceptions.FileError import FileError
import re

class XLSDataReader(BaseDataReader):
  name = "XLS Data Reader"
  description = "Reads Excel (XLS and XLSX) formattted data"
  type = "Excel"

  priority = 10

  def __init__(self, filepath=None):
    super(XLSDataReader, self).__init__(filepath)

  #
  @classmethod
  def identify(cls, filepath):
    try:
      book = xlrd.open_workbook(filepath)
      return True
    except:
      return False

  #
  def read(self, filepath):
    self.input_file = None

    try:
      book = xlrd.open_workbook(filepath)
      self.input_file = book.sheet_by_index(0)
    except:
      pass

    super(XLSDataReader, self).read(filepath)

    h = self.input_file.row(0)

    h = [str(a.value) for a in h]
    print h
    if len(filter(lambda x: re.match(r'^[\d]$', x), h)) > 0 or len(set(h)) < len(h):
      # no headers
      self.headers = [str(x) for x in range(1, len(h))]
    else:
      self.headers = h

    if self.input_file:
      return True
    else:
      return False

  #
  def getRows(self, rows=None, start=0):
    if self.input_file is None:
      raise FileError("No file loaded", "XLSDataReader.getRows")

    nrows = self.input_file.nrows
    if rows is not None and rows < nrows:
      nrows = rows
    ncols = self.input_file.ncols

    file_data = []

    for rx in range(start, nrows):

      row = []
      for cx in range(ncols):
        cell = self.input_file.cell_value(rowx=rx, colx=cx)
        if isinstance(cell, float):
          if int(cell) == cell:
              cell = int(cell)

        row.append(cell)
      if row == self.headers:
        continue
      file_data.append(row)

    return file_data
