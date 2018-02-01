from string import Template
import os
import inspect

utildir = os.path.dirname(os.path.abspath(inspect.stack()[0][1])).split("/")
del utildir[-1:-2]

def email_template(name, type, values):
    with open("/".join(utildir) + "/../../templates/email/" + name + "." + type, 'r') as template_file:
        template_file_content = template_file.read()

    tmpl = Template(template_file_content)
    return tmpl.safe_substitute(values)