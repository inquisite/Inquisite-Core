import os
import json
import sys
import unittest
from BaseTest import BaseTest


class SchemaManagerTests(BaseTest):
  def setUp(self):
    self.plugin_base = PluginBase(package='lib.plugins.dataTypes')
    self.plugin_source = self.plugin_base.make_plugin_source(
      searchpath=['lib/plugins/dataTypes'])
    self.dataTypePlugins = {}
    self.pluginsAreLoaded = False
    self.loadDataTypePlugins()


  def tearDown(self):
    super(RepoTest, self).tearDown()

  def test_repositories(self):
    # Get repo - bad user id
    rv = self.client.get('/repositories', headers={"Authorization": "Bearer " + self.token})
    retobj = json.loads(rv.data)
    assert isinstance(retobj['repos'], list) == True

    self.logout(self.token)

if __name__ == '__main__':
    unittest.main()