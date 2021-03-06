import os
import json
import sys
import unittest
from BaseTest import BaseTest


class BannerTests(BaseTest):
  def test_banner(self):
    # Get repo - bad user id
    rv = self.client.get('/')
    retobj = json.loads(rv.data)
    assert isinstance(retobj['repos'], list) == True

if __name__ == '__main__':
    unittest.main()