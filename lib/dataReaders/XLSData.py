import xlrd

class XLSReader():
  #def __init__(self, input_file):
  #  self.input_file = input_file

  @classmethod
  def getRows(cls, filepath, rows=None, start=0):
    book = xlrd.open_workbook(filepath)
    sh = book.sheet_by_index(0)

    nrows = sh.nrows
    if rows is not None and rows < nrows:
      nrows = rows
    ncols = sh.ncols

    file_data = []

    for rx in range(start, nrows):

      row = []
      for cx in range(ncols):
        row.append( sh.cell_value(rowx=rx, colx=cx) )

      file_data.append(row)


    return file_data

