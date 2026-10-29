"""
Create initial administrator account for SmartMed AI.
"""
import getpass
import os
import sys
from django.contrib.auth.hashers import make_password

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from database.repositories.user_repository import UserRepository
from database.repositories.audit_repository import AuditRepository

def create_admin_user(username="admin", email="admin@smartmed.ai", password=password):
    existing = UserRepository.get_by_username(username)
    if existing:
        print(f"User '{username}' already exists in MongoDB.")
        return existing

    hashed = make_password(password)
    user_doc = UserRepository.create_user(
        username=username,
        email=email,
        password_hash=hashed,
        role="admin",
        full_name="Lead Research Administrator"
    )

    AuditRepository.record_event(
        actor="system_init",
        action="ADMIN_INITIALIZED",
        target_id=user_doc["user_id"],
        metadata={"username": username}
    )

    print(f"Successfully created administrator account!")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Role: admin")
    return user_doc

if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "admin"
    p = sys.argv[2] if len(sys.argv) > 2 else getpass.getpass("Admin password: ")
    create_admin_user(username=u, password=p)
