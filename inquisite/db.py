from neo4j.v1 import GraphDatabase, basic_auth, ResultError
from inquisite.config import app_config

driver = GraphDatabase.driver(app_config['database_url'], auth=basic_auth(app_config['database_user'],app_config['database_pass']))
db = driver.session()
