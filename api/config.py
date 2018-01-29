import os
import inspect
import json

apidir = os.path.dirname(os.path.abspath(inspect.stack()[0][1])).split("/")
del apidir[-1]
app_config = json.load(open("/".join(apidir) + '/config.json'));