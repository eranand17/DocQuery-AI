
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count,Q
from django.shortcuts import render

from documents.models import Document

def home(request):
    return render(request, "dashboard/home.html")

@staff_member_required
def admin_dashboard(request):
    stats = Document.objects.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status=Document.Status.PENDING)),
        approved=Count("id", filter=Q(status=Document.Status.APPROVED)),
        rejected=Count("id", filter=Q(status=Document.Status.REJECTED)),

    )
    documents = Document.objects.select_related("uploaded_by").order_by("-uploaded_at")
    return render(
        request,
        "dashboard/admin_dashboard.html",
        {
            "stats": stats,
            "documents": documents,
        },
    )
