import re
import json


# Flatten JSON
def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#
#
#
def email_domain_is_allowed(email):
    print "MEH"
    configFile = open('./config.json')
    config = json.load(configFile)
    if 'registration_email_domains' in config.keys():
        domains = config['registration_email_domains']
        print domains
        if len(domains) == 0:
            return True     # empty list = allow all domains

        for d in domains:
            if re.search(re.escape(d) + "$", email):
                return True
    else:
        return True     # no config = allow all domains

    return False