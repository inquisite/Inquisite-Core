from api.config import app_config
from passlib.hash import sha256_crypt
from lib.exceptions.AuthError import AuthError
from lib.exceptions.FindError import FindError
from lib.utils.Db import db
from flask_jwt_extended import JWTManager, jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity, get_raw_jwt, revoke_token

from lib.utils.UtilityHelpers import is_number
from lib.utils.MailHelpers import send_mail
import uuid



class AuthManager:
    # For now all class methods are going to be static
    def __init__():
        pass

    #
    @staticmethod
    def login(username, password):
        if username is not None and password is not None:
            db_user = db.run(
                "MATCH (n:Person) WHERE n.email={username} RETURN n.name AS name, n.email AS email, n.password AS password, ID(n) AS user_id",
                {"username": username})

            for person in db_user:
                if sha256_crypt.verify(password, person['password']):
                    return {"access_token": create_access_token(identity=username), "refresh_token": create_refresh_token(identity=username), "user_id": person["user_id"]}
            raise AuthError("Username or password is incorrect")
        else:
            raise AuthError("Username and Password are required")

        raise AuthError("Authentication failed")

    @staticmethod
    def sendPasswordReset(email_address):
        reset_key = uuid.uuid4().hex
        result = db.run("MATCH (p:Person) WHERE p.email={email} AND (p.is_disabled = NULL OR p.is_disabled = 0) SET p.password_reset_key = {reset_key} RETURN ID(p) AS id, p.email AS email",
                        {"email": email_address, "reset_key": reset_key})
        for p in result:
            try:
                send_mail(email_address, None, "Password reset request for " + email_address, "reset_password", {"email": email_address, "reset_url": app_config["base_url"] + "/#/password/reset?reset=" + reset_key})
            except Exception as e:
                # SMTP error
                raise AuthError("Could not send email: " + e.message)
            break
        # If email address isn't available for user return all is well (don't throw exception) but don't send anything
        # as we don't want or need to indicate to the caller that the address was invalid
        return {"recipient": email_address}

    @staticmethod
    def setPassword(person_id, password):
        # TODO: verify user has access to update password...
        if password is not None:
            if is_number(person_id):
                find_str = "ID(p)={person_id}"
            else:
                find_str = "p.password_reset_key = {person_id}"

            db_password_hash = ''
            # check if password matches person_id
            result = db.run("MATCH (p:Person) WHERE " + find_str + " RETURN p.password AS password",
                            {"person_id": person_id})
            for p in result:
                db_password_hash = p['password']

            if db_password_hash != '':
                # hash new password and update DB
                new_pass_hash = sha256_crypt.hash(password)

                if db_password_hash == new_pass_hash:
                    return True

                result = db.run("MATCH (p:Person) WHERE " + find_str + " SET p.password = {new_pass_hash}, p.password_reset_key = '' RETURN p",
                                {"person_id": person_id, "new_pass_hash": new_pass_hash})

                # Check we updated something
                summary = result.consume()
                if summary.counters.properties_set >= 1:
                    return True
                return False

            else:
                raise FindError("No user found")

        else:
            raise AuthError("Password is empty")
