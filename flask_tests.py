# Flask Test Suite Skeleton
import os
import json
import unittest

config = json.load(open('./config.json'))

from api import app

class FlaskTestCase(unittest.TestCase):

  def setUp(self):
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = config['auth_secret']
    self.app = app.test_client()

  def tearDown(self):
    app.config['TESTING'] = False
    self.app = None

  def login(self, username, password):
    return self.app.post('/login', data = dict(
      username = username,
      password = password
    ), follow_redirects = True)

  def logout(self, access_token):
    return self.app.get('/logout', environ_base={"Authorization": "Bearer " + access_token}, follow_redirects = True)

  #-----------------------------------
  # Inquisite Core API Endpoint Tests
  #-----------------------------------

  # make sure our base url just returns something
  def test_base_url(self):
    rv = self.app.get('/')
    assert rv.data != ''      

  def test_login_logout(self):

    # Test Login
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)

    assert retobj['access_token'] != ''
    assert retobj['user_id'] is not None
    assert retobj['email'] != ''

    # Test Logout -- currently doesn't return anything
    rv = self.logout(retobj['access_token'])
    print rv

    # Bad username
    rv = self.login("notauser", "notauserpassword")
    retobj = json.loads(rv.data)
 
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    # Bad password
    rv = self.login(config['unit_test_user'], "Thisisabadpassword")
    retobj = json.loads(rv.data)

    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''
 
  # People
  def test_people(self):
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)
    access_token = retobj['access_token']

    rv = self.app.get('/people', headers={"Authorization": "Bearer " + access_token}, follow_redirects = True)
    retobj = json.loads(rv.data)

    assert retobj['status'] == 'ok'
    assert isinstance(retobj['people'], list) == True
    assert len(retobj['people']) >= 1

    self.logout(access_token)

  def test_single_person_data(self):
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)
    access_token = retobj['access_token']

    rv = self.app.post('/people/' + config['unit_test_userid'], headers={"Authorization": "Bearer " + access_token}, follow_redirects = True)
    retobj = json.loads(rv.data)

    assert retobj['status'] == "ok"
    assert retobj['name'] != ''
    assert retobj['email'] != ''
    assert retobj['url'] != ''
    assert retobj['location'] != ''
    assert retobj['tagline'] != ''

    # Test Bad user id 

    rv = self.app.post('/people/0012', headers={"Authorization": "Bearer " + access_token}, follow_redirects = True)
    retobj = json.loads(rv.data)

    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    self.logout(access_token)


  def test_add_edit_delete_person(self):
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)
    access_token = retobj['access_token']

    print " TESTING EMPTY PERSON "
    # Add Person - empty values 
    rv = self.app.post('/people/add', data = dict(
      name     = None,
      location = None, 
      email    = None,
      url      = None,
      tagline  = None,
      password = None
    ))

    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''


    print " TESTING REAL DATA "

    # Add Person 
    test_name = 'tester'
    test_location = 'testing town'
    test_email = 'test@email.com'
    test_url = 'http://test.com'
    test_tagline = 'this is just a test'
    test_password = 'testpass'

    rv = self.app.post('/people/add', data = dict(
      name     = test_name,
      location = test_location,
      email    = test_email,
      url      = test_url,
      tagline  = test_tagline, 
      password = test_password
    ))

    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert retobj['msg'] != ''
    user_id = str(retobj['person']['user_id'])

    # Edit Person - Empty values
    rv = self.app.post('/people/' + user_id + '/edit', headers={"Authorization": "Bearer " + access_token},
      data = dict(
        name = None,
        location = None,
        email = None,
        url = None,
        tagline = None
    )) 
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''


    # Edit Person - Bad user_id
    rv = self.app.post('/people/0012/edit', headers={"Authorization": "Bearer " + access_token},
      data = dict(
      name = 'noone',
      location = 'nowhere',
      email = 'noone@email.com',
      url = 'http://nothere.com',
      tagline = 'daves not here'
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''


    # Edit Person
    rv = self.app.post('/people/' + user_id + '/edit', headers={"Authorization": "Bearer " + access_token},
      data = dict(
        name = 'edited tester',
        location = 'i moved',
        email = 'editedtest@email.com',
        url = 'http://newtestwebsite.com',
        tagline = 'new slogan, new me'
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert retobj['msg'] != '' 

    rv = self.app.post('/people/7609/delete', headers={"Authorization": "Bearer " + access_token})

    # Delete Person - Bad user_id
    rv = self.app.post('/people/0012/delete', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)

    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    # Delete Person
    rv = self.app.post('/people/' + user_id + '/delete', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert retobj['msg'] != ''


    self.logout(access_token)

  # User Repos
  def test_repos(self):
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)
    access_token = retobj['access_token']

    # Get repo - bad user id
    rv = self.app.get('/people/0012/repos', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)

    assert retobj['status'] == 'ok'
    assert isinstance(retobj['repos'], list) == True

    # get repo
    rv = self.app.get('/people/7585/repos', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)

    assert retobj['status'] == 'ok'
    assert isinstance(retobj['repos'], list) == True
    assert len(retobj['repos']) >= 1

    self.logout(access_token)

  # Change user Password
  def test_change_user_passowrd(self):
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)
    access_token = retobj['access_token']

    # No Passwords
    rv = self.app.post('/people/7585/set_password', headers={"Authorization": "Bearer " + access_token}, data=dict(
      password = None,
      new_password = None
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''


    # No New Password
    rv = self.app.post('/people/7585/set_password', headers={"Authorization": "Bearer " + access_token}, data=dict(
      password = 'password',
      new_password = None
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != '' 

    # Same Passwords
    rv = self.app.post('/people/7585/set_password', headers={"Authorization": "Bearer " + access_token}, data=dict(
      password = 'password',
      new_password = 'password'
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''  

    # Bad user id
    rv = self.app.post('/people/0012/set_password', headers={"Authorization": "Bearer " + access_token}, data=dict(
      password = 'password',
      new_password = 'password'
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''


    # Change Passwords - success
    rv = self.app.post('/people/' + config['unit_test_userid'] + '/set_password', headers={"Authorization": "Bearer " + access_token}, 
      data=dict(
        password = config['unit_test_pass'],
        new_password = 'new_password'
      )
    )
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert retobj['msg'] != ''

    # .. put it back
    rv = self.app.post('/people/' + config['unit_test_userid'] + '/set_password', headers={"Authorization": "Bearer " + access_token}, 
      data=dict(
        password = 'new_password',
        new_password = config['unit_test_pass']
      )
    )
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert retobj['msg'] != ''


    self.logout(access_token)

  # Organizations
  def test_organizations(self):
    rv = self.login(config['unit_test_user'], config['unit_test_pass'])
    retobj = json.loads(rv.data)
    access_token = retobj['access_token']
 
    # add organizations - empty data check
    rv = self.app.post('/organizations/add', headers={"Authorization": "Bearer " + access_token}, data=dict(
      name = None,
      location = None,
      email = None,
      url = None,
      tagline = None
    )) 
    retobj = json.loads(rv.data)
    
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    # add organizations
    rv = self.app.post('/organizations/add', headers={"Authorization": "Bearer " + access_token}, data=dict(
      name = "Test Organization",
      location = "Testing Town",
      email = "testorg@testingorg.com",
      url = "http://testingorg.com",
      tagline = "This is only a test"
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == "ok"
    assert isinstance(retobj['organization'], dict) == True
    org_id = str(retobj['organization']['org_id'])


    # list organizations
    rv = self.app.get('/organizations', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data) 

    assert retobj['status'] == "ok"
    assert isinstance(retobj['orgs'], list) == True
    assert len(retobj['orgs']) >= 1

    # get single organization
    rv = self.app.get('/organizations/' + org_id, headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)
    assert retobj['status'] == "ok"
    assert retobj['msg'] != ''
    assert isinstance(retobj['organization'], dict) == True

    # get single orgainizaton - bad org_id
    rv = self.app.get('/organizations/101010', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    # edit organizations - empty case
    rv = self.app.post('/organizations/' + org_id + '/edit', headers={"Authorization": "Bearer " + access_token},
      data=dict(
        name = None,
        location = None,
        email = None,
        url = None,
        tagline = None
    ))
    retobj = json.loads(rv.data) 
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    # edit organizations - bad org_id
    rv = self.app.post('/organizations/101010/edit', headers={"Authorization": "Bearer " + access_token},
      data=dict(
        name = "New Org name",
        location = "We changed it",
        email = "oops@organization.com",
        url = "https://testorg.org",
        tagline = "New words"
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'err'
    assert retobj['msg'] != ''

    # edit organizations
    rv = self.app.post('/organizations/' + org_id + '/edit', headers={"Authorization": "Bearer " + access_token},
      data=dict(
        name = "New Org name",
        location = "We changed it",
        email = "oops@organization.com",
        url = "https://testorg.org",
        tagline = "New words"
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert retobj['msg'] != ''
    assert isinstance(retobj['org'], dict) == True
    assert retobj['org']['name'] != ''

    # create test repo

    # add organization repo    
    rv = self.app.post('/organizations/' + org_id + '/repos/add', headers={"Authorization": "Bearer " + access_token},
      data=dict(
      name = None
    ))
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'


    # list organization repos
    rv = self.app.get('/organizations/' + org_id + '/repos', headers={"Authorization": "Bearer " + access_token})
    retobj = json.loads(rv.data)
    assert retobj['status'] == 'ok'
    assert isinstance(retobj['repos'], list) == True

    # delete organization repo relationship

    # destory test repo

    # create test org person 

    # add organization person
 
    # list organization people

    # delete organization person

    # destroy test org person

    # delete organization 



    self.logout(access_token)

if __name__ == '__main__':
  unittest.main()
