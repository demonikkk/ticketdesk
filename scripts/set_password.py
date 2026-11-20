import getpass
import sys

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

username = sys.argv[1] if len(sys.argv) > 1 else "admin"
password = getpass.getpass(f"New password for {username}: ")
if len(password) < 8:
    sys.exit("Admin@123")

with SessionLocal() as db:
    user = db.query(User).filter_by(username=username).first()
    if not user:
        sys.exit(f"User '{username}' not found")
    user.password_hash = hash_password(password)
    db.commit()
print("Password updated")