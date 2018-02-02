from api.config import app_config
from string import Template
import os
import inspect
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from lib.exceptions.MailerError import MailerError

utildir = os.path.dirname(os.path.abspath(inspect.stack()[0][1])).split("/")
del utildir[-1:-2]

#
# Load and process email templates (stored in templates/email)
#
def email_template(name, type, values):
    with open("/".join(utildir) + "/../../templates/email/" + name + "." + type, 'r') as template_file:
        template_file_content = template_file.read()

    tmpl = Template(template_file_content)
    return tmpl.safe_substitute(values)

#
# Send email alerts
#
def send_mail(to_addr, from_addr, subject, template_name, template_values):
    if from_addr is None:
        from_addr = app_config["email_from_address"]
    try:
        server = smtplib.SMTP(app_config["smtp_server"], app_config["smtp_port"])
        server.ehlo()
        # secure our email with tls encryption
        server.starttls()
        # re-identify ourselves as an encrypted connection
        server.ehlo()
        server.login(app_config["smtp_user"], app_config["smtp_password"])

        msg = MIMEMultipart()  # create a message
        message_html = email_template(template_name, "html", template_values)

        # setup the parameters of the message
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = "[Inquisite] " + subject

        # add in the message body
        msg.attach(MIMEText(message_html, 'html'))

        server.sendmail(from_addr, to_addr, msg.as_string())
        server.quit()
    except Exception as e:
        # SMTP error
        raise MailerError("Could not send email: " + e.message)