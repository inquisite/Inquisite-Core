import os
import json
import sys
import unittest
from BaseTest import BaseTest
from lib.managers.SchemaManager import SchemaManager


class SchemaManagerTests(BaseTest):
  def setUp(self):
    self.schema_manager = SchemaManager()
    super(SchemaManagerTests, self).setUp()


  def tearDown(self):
    super(SchemaManagerTests, self).tearDown()

  def test_getDataTypes(self):
    print "Data types are: "
    print SchemaManager.getDataTypes()

    for x in SchemaManager.getDataTypes():
      p = SchemaManager.getDataTypePlugin(x)
      print p.getSettingsList()
      i = SchemaManager.getDataTypeInstance(x)
      i.validateSettings({"min_length": "0", "max_length": "100"})
    return True

if __name__ == '__main__':
    unittest.main()