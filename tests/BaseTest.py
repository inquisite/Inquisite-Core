import os
import json
import unittest
import sys

sys.path.append(".")
from app import app

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.configFile = open('./config.json')
        self.config = json.load(self.configFile)

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = self.config['auth_secret']

    def tearDown(self):
        self.app.config['TESTING'] = False
        self.app = None
        self.configFile.close()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self, access_token):
        return self.client.get('/logout', environ_base={"Authorization": "Bearer " + access_token}, follow_redirects=True)