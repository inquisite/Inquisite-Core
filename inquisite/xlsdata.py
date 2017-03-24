import xlrd

class XlsHandler():

  input_file = None

  def __init__(self, input_file):
    self.input_file = input_file

  def read_file(self):
    book = xlrd.open_workbook(self.input_file)
    sh = book.sheet_by_index(0)

    nrows = sh.nrows
    ncols = sh.ncols

    file_data = []

    for rx in range(nrows):

      row = []
      for cx in range(ncols):
        row.append( sh.cell_value(rowx=rx, colx=cx) )

      file_data.append(row)


    return file_data

