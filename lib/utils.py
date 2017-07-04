import re

#
# Extract into a dictionary repeating parameters encoded thusly:
#
# name[0][key1] = some-value
# name[0][key2] = some-value
# name[0][key3] = some-value
# name[1][key1] = some-value
# name[1][key2] = some-value
# name[1][key3] = some-value
#
# Continuous numbering from zero of parameters is assumed.
#
def extractRepeatingParameterBlocksFromRequest(req, name):
    acc = {}
    for k in req.form:
        m = re.match("{0}\[([\d]+)\]\[([A-Za-z0-9\-_]+)\]".format(name), k)
        if m:
            i = int(m.group(1))
            sn = m.group(2)

            if i not in acc:
                acc[i] = {}
            acc[i][sn] = req.form.get(k)

    return acc

#
#
#
def extractRepeatingParameterFromRequest(req, name):
    acc = []
    for k in req.form:
        m = re.match("{0}\[([\d]+)\]".format(name), k)
        if m:
            acc.append(req.form.get(k))

    return acc