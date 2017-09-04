import re

#
#
#
def makeDataMapForCypher(data, mode="I", prefix=None):
    flds = []
    for i in data.keys():
        if (i == '_ID'):
            continue
        fname = re.sub(r"[^A-Za-z0-9_]", "_", i)  # remove non-alphanumeric characters from field names
        fname = re.sub(r"^([\d]+)", "_\1",
                       fname).strip()  # Neo4j field names cannot start with a number; prefix such fields with an underscore

        placeholder = fname
        if prefix is not None:
            fname = prefix + fname

        if mode == "U":
            flds.append(fname + " = {" + placeholder + "}")
        else:
            flds.append(fname + ":{" + placeholder + "}")



    if mode == "U":
        return ",".join(flds)
    else:
        return "{" + ",".join(flds) + "}"
