from passlib.apps import custom_app_context as pwd_context

class User(object):

  def __init__(self):
    self.password_hash = ''

  def hash_password(self, password):
    self.password_hash = pwd_context.encrypt(password)

  def verify_password(password, db_hash):

    print "in User.verify_password"
    print "verify password: " + password
    print "verify hash: " + db_hash

    result = pwd_context.verify(password, db_hash)

    print "result: " + result

    return result
