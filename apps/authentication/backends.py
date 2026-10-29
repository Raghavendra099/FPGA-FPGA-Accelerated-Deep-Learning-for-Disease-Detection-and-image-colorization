"""
MongoDB Authentication Backend for SmartMed AI.
Validates credentials against MongoDB users collection using Django's PBKDF2/bcrypt hashing.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from database.repositories.user_repository import UserRepository
from database.repositories.audit_repository import AuditRepository

class MongoAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        user_doc = UserRepository.get_by_username(username)
        if not user_doc or not user_doc.get("is_active", True):
            return None

        password_hash = user_doc.get("password_hash", "")
        # Check password against stored hash
        if check_password(password, password_hash):
            UserRepository.update_last_login(username)
            # Sync / fetch Django User for session management
            user, created = User.objects.get_or_create(username=user_doc["username"])
            if created:
                user.email = user_doc.get("email", "")
                user.first_name = user_doc.get("full_name", "")
                if user_doc.get("role") == "admin":
                    user.is_staff = True
                    user.is_superuser = True
                user.set_unusable_password()
                user.save()
            else:
                # Update staff/superuser status according to MongoDB role
                is_admin = user_doc.get("role") == "admin"
                if user.is_staff != is_admin:
                    user.is_staff = is_admin
                    user.is_superuser = is_admin
                    user.save()

            if request:
                request.session["mongo_user_id"] = user_doc.get("user_id")
                request.session["mongo_role"] = user_doc.get("role", "reviewer")
                request.session["mongo_username"] = user_doc.get("username")
                request.session["mongo_full_name"] = user_doc.get("full_name", username)
                AuditRepository.record_event(
                    actor=username,
                    action="LOGIN_SUCCESS",
                    metadata={"role": user_doc.get("role", "reviewer")},
                    ip_address=request.META.get("REMOTE_ADDR")
                )
            return user
        else:
            if request:
                AuditRepository.record_event(
                    actor=username,
                    action="LOGIN_FAILED",
                    metadata={"reason": "Invalid password"},
                    ip_address=request.META.get("REMOTE_ADDR")
                )
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
