"""
Authentication views for SmartMed AI.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from database.repositories.user_repository import UserRepository
from database.repositories.audit_repository import AuditRepository

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next", "dashboard:index")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please verify credentials.")

    return render(request, "authentication/login.html")

def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        full_name = request.POST.get("full_name", "").strip()
        role = request.POST.get("role", "reviewer")

        if role not in ("reviewer", "admin"):
            role = "reviewer"

        if not username or len(username) < 3:
            messages.error(request, "Username must be at least 3 characters long.")
            return render(request, "authentication/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "authentication/register.html")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, "authentication/register.html")

        # Check existing user
        if UserRepository.get_by_username(username):
            messages.error(request, "A user with this username already exists.")
            return render(request, "authentication/register.html")

        hashed = make_password(password)
        user_doc = UserRepository.create_user(
            username=username,
            email=email,
            password_hash=hashed,
            role=role,
            full_name=full_name
        )

        AuditRepository.record_event(
            actor=username,
            action="USER_REGISTERED",
            metadata={"role": role, "email": email},
            ip_address=request.META.get("REMOTE_ADDR")
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("auth:login")

    return render(request, "authentication/register.html")

def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        AuditRepository.record_event(
            actor=username,
            action="LOGOUT",
            ip_address=request.META.get("REMOTE_ADDR")
        )
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect("auth:login")
