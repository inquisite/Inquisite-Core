from api.config import app_config
from passlib.hash import sha256_crypt
from lib.exceptions.AuthError import AuthError
from lib.exceptions.FindError import FindError
from lib.utils.Db import db
from flask_jwt_extended import JWTManager, jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity, get_raw_jwt, revoke_token
import smtplib
from lib.utils.MailHelpers import email_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



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
        result = db.run("MATCH (p:Person) WHERE p.email={email} AND (p.is_disabled = NULL OR p.is_disabled = 0) RETURN ID(p) AS id, p.email AS email",
                        {"email": email_address})
        for p in result:
            try:
                server = smtplib.SMTP(app_config["smtp_server"], app_config["smtp_port"])
                server.ehlo()
                # secure our email with tls encryption
                server.starttls()
                # re-identify ourselves as an encrypted connection
                server.ehlo()
                server.login(app_config["smtp_user"], app_config["smtp_password"])

                msg = MIMEMultipart()  # create a message
                message_html = email_template("reset_password", "html", {"email": email_address})

                # setup the parameters of the message
                msg['From'] = app_config["email_from_address"]
                msg['To'] = email_address
                msg['Subject'] = "[Inquisite] Password reset request for " + email_address

                # add in the message body
                msg.attach(MIMEText(message_html, 'html'))

                server.sendmail(app_config["email_from_address"], email_address, msg.as_string())
                server.quit()
                return {"recipient": email_address, "person_id": p['id']}
            except Exception as e:
                # SMTP error
                raise AuthError("Could not send email: " + e.message)
            break
        # Email address isn't available for user
        raise AuthError("Could not send email")

    @staticmethod
    def setPassword(person_id, password, new_password):
        if password is not None and new_password is not None:

            # check if password and new pass are the same
            if password != new_password:

                db_password_hash = ''
                # check if password matches person_id
                result = db.run("MATCH (p:Person) WHERE ID(p)={person_id} RETURN p.password AS password",
                                {"person_id": person_id})
                for p in result:
                    db_password_hash = p['password']

                if db_password_hash != '':

                    # hash new password and update DB
                    new_pass_hash = sha256_crypt.hash(new_password)

                    result = db.run("MATCH (p:Person) WHERE ID(p)={person_id} SET p.password = {new_pass_hash}",
                                    {"person_id": person_id, "new_pass_hash": new_pass_hash})

                    # Check we updated something
                    summary = result.consume()
                    if summary.counters.properties_set >= 1:
                        return True
                    return False

                else:
                    raise FindError("No user found")

            else:
                raise AuthError("New Password is the same as current password")

        else:
            raise AuthError("Password and New Password needed to change password")