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
    print self.schema_manager.getDataTypes()
    return True

if __name__ == '__main__':
    unittest.main()