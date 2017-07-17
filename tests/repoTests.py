import os
import json
import sys
import unittest
from baseTest import BaseTest


class RepoTest(BaseTest):
  def setUp(self):
    super(RepoTest, self).setUp()
    rv = self.login(self.config['unit_test_user'], self.config['unit_test_pass'])
    retobj = json.loads(rv.data)
    self.token = retobj['access_token']


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