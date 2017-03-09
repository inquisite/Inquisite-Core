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

    print "XlsHandler opened " + str(self.input_file) + " with Rows: " + str(nrows) + " and Cols: " + str(ncols)
    print "Assuming First column data are field names ..."

    field_names = []

    for rx in range(nrows):
      field_names.append( sh.cell_value(rowx=rx, colx=0) )


    print "Fields Names found: "
    print field_names 

    return field_names

