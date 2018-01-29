import sys
sys.path.append("../.")
from lib.utils.Db import db

email = None
if len(sys.argv) > 1:
    email = sys.argv[1]
if email is None or email == "":
    sys.stdout.write("You must specify an email address of a current user\n")
    sys.exit(1)

res = db.run("MATCH (u:Person) WHERE u.email = {email} RETURN u.email, u.is_admin", {"email": email})

if res is None:
    sys.stdout.write("Query failed\n")
    sys.exit(1)

found = False
for r in res:
    found = True
    print r
    if "u.is_admin" in r and r["u.is_admin"] == 1:
        sys.stdout.write("User " + email + " is already admin\n")
    else:
        db.run("MATCH (u:Person) WHERE u.email = {email} SET u.is_admin = 1 RETURN u", {"email": email})
        sys.stdout.write("User " + email + " set to admin\n")
        break

if found is False:
    sys.stdout.write("User not found\n")
    sys.exit(1)