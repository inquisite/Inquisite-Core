import os
import json
import sys
import unittest
from BaseTest import BaseTest


class AuthManagerTests(BaseTest):
  def test_login_logout(self):
    # Test Login
    rv = self.login(self.config['unit_test_user'], self.config['unit_test_pass'])
    retobj = json.loads(rv.data)
    assert retobj['access_token'] != ''

    # Test Logout -- currently doesn't return anything
    rv = self.logout(retobj['access_token'])
    print(rv)

    # Bad username
    rv = self.login("notauser", "notauserpassword")
    retobj = json.loads(rv.data)

    assert retobj['msg'] != ''

    # Bad password
    rv = self.login(self.config['unit_test_user'], "Thisisabadpassword")
    retobj = json.loads(rv.data)

    assert retobj['msg'] != ''

if __name__ == '__main__':
    unittest.main()