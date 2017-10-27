import json
from lib.plugins.dataReaders.BaseDataReader import BaseDataReader
from lib.exceptions.FileError import FileError
import collections

class GeoJSONDataReader(BaseDataReader):
  name = "GeoJSON Data Reader"
  description = "Reads GeoJSON formatted data"

  priority = 20

  def __init__(self, filepath=None):
    super(GeoJSONDataReader, self).__init__(filepath)

  #
  @classmethod
  def identify(cls, filepath):
    try:
        d = json.load(open(filepath, "rb"))
        if "type" in d and "features" in d and d["type"] == "FeatureCollection" and len(d["features"]) > 0:
          return True
    except Exception as e:
        pass
    return False

  #
  def read(self, filepath):
    self.input_file = None

    try:
      self.input_file = json.load(open(filepath, "rb"))
    except:
      pass

    super(GeoJSONDataReader, self).read(filepath)

    self.headers = self.extractHeaders()

    if self.input_file:
      return True
    else:
      return False

  def extractHeaders(self):
      for row in self.input_file["features"]:
          headers = row["properties"].keys()[:]
          if "data" in row["properties"] and isinstance(row["properties"]["data"], dict):
            for k, v in row["properties"]["data"].iteritems():
                headers.append(k)
          headers.append("geometry")

          return headers

  def getRows(self, rows=None, start=0):
    if self.input_file is None:
      raise FileError("No file loaded", "GeoJSONDataReader.getRows")
    file_data = []

    c = 0
    for row in self.input_file["features"]:
      c = c + 1
      if start is not None and c < start:
        continue
      if rows is not None and c > rows:
        break
      if "properties" not in row:
        continue

      # process geometry
      geometry = ""
      if "geometry" in row:
        if row["geometry"]["type"] == "Polygon":
          # TODO: handle multiple polygons
          acc = []
          for coord in row["geometry"]["coordinates"][0]:
            acc.append(",".join(str(x) for x in coord))
          geometry = ";".join(acc)

      # flatten properties
      row_proc = row["properties"]
      row_proc["geometry"] = geometry
      if "data" in row_proc and isinstance(row_proc["data"], dict):
        for k, v in row_proc["data"].iteritems():
          row_proc[k] = v
        del row_proc["data"]

      file_data.append(row_proc)

    #print file_data
    return file_data
