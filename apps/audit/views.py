"""
Audit trail inspection views.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from database.repositories.audit_repository import AuditRepository

@login_required
def index_view(request):
    events = AuditRepository.list_recent(limit=100)
    return render(request, "dashboard/audit_list.html", {"events": events})
