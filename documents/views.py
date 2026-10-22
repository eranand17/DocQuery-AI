import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import DocumentForm
from .models import Document


logger = logging.getLogger(__name__)


@login_required
def upload_document(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.uploaded_by = request.user
                document.save()

                messages.success(
                    request,
                    "Your document was uploaded and is awaiting admin approval.",
                )
                return redirect("upload_document")

            except Exception:
                logger.exception(
                    "Document upload failed for user ID %s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "Upload failed. Please try again.",
                )
        else:
            messages.error(
                request,
                "Please correct the errors below.",
            )
    else:
        form = DocumentForm()

    return render(
        request,
        "documents/upload.html",
        {"form": form},
    )


@login_required
def my_documents(request):
    documents = Document.objects.filter(
        uploaded_by=request.user
    ).order_by("-uploaded_at")

    return render(
        request,
        "documents/my_documents.html",
        {"documents": documents},
    )
