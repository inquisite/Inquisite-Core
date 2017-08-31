import re

#
#
#
def makeDataMapForCypher(data):
    flds = []
    for i in data.keys():
        if (i == '_ID'):
            continue
        fname = re.sub(r"[^A-Za-z0-9_]", "_", i)  # remove non-alphanumeric characters from field names
        fname = re.sub(r"^([\d]+)", "_\1",
                       fname).strip()  # Neo4j field names cannot start with a number; prefix such fields with an underscore

        flds.append(fname + ":{" + fname + "}")
    return "{" + ",".join(flds) + "}"
