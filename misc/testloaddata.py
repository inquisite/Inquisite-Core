import re

import xlrd


def get_field_names(input_file):
    book = xlrd.open_workbook(input_file)
    sh = book.sheet_by_index(0)

    nrows = sh.nrows
    ncols = sh.ncols

    #print "XlsHandler opened " + str(input_file) + " with Rows: " + str(nrows) + " and Cols: " + str(ncols)
    #print "Assuming First column data are field names ..."

    field_names = []

    for cx in range(ncols):
        field_names.append(sh.cell_value(rowx=0, colx=cx))

    #print "Fields Names found: "
    #print field_names

    return field_names

def read_file(input_file):
    book = xlrd.open_workbook(input_file)
    sh = book.sheet_by_index(0)

    nrows = sh.nrows
    ncols = sh.ncols

    print "XlsHandler opened " + str(input_file) + " with Rows: " + str(nrows) + " and Cols: " + str(ncols)
    print "Assuming First column data are field names ..."

    field_names = get_field_names(input_file)

    data = []
    for rx in range(nrows):
        row = {}
        for cx in range(ncols):
            row[re.sub(r'[^A-Za-z0-9_\-]+', '_', field_names[cx]).lower()] = sh.cell_value(rowx=rx, colx=cx)

        data.append(row)
    #print "Fields Names found: "
    #print field_names

    return data

field_names = get_field_names("rothko.xlsx")
print field_names
data= getRepositoryByCode("Rothko works on paper")

repo_id = data['payload']['repo_id']

addType(repo_id, "Artwork", "artwork", "Artworks in collection")
for f in field_names:
    addField(repo_id, 'artwork', f, re.sub(r'[^A-Za-z0-9_\-]+', '_', f).lower(), 'TEXT', '?')

data = read_file("rothko.xlsx")
for d in data:
    addDataToRepo(repo_id, 'artwork', d)