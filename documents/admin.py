import logging

from django.contrib import admin, messages
from django.utils import timezone

from documents.models import Document
from rag.pipeline import rag_pipeline


logger = logging.getLogger(__name__)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "uploaded_by",
        "status",
        "uploaded_at",
        "reviewed_at",
    )
    list_filter = ("status", "uploaded_at", "reviewed_at")
    search_fields = ("title", "uploaded_by__username")
    readonly_fields = ("uploaded_at", "reviewed_at")
    actions = ("approve_documents", "reject_documents")

    @admin.action(description="Approve and process selected documents")
    def approve_documents(self, request, queryset):
        allowed_statuses = [
            Document.Status.PENDING,
            Document.Status.APPROVED,
            Document.Status.ERROR,
        ]

        processed_count = 0
        failed_count = 0
        skipped_count = 0

        for document in queryset:
            if document.status not in allowed_statuses:
                skipped_count += 1
                continue

            try:
                document.status = Document.Status.PROCESSING
                document.reviewed_at = timezone.now()
                document.save(update_fields=["status", "reviewed_at"])

                result = rag_pipeline.process_pdf(
                    document.file.path,
                    document.id,
                )

                document.status = Document.Status.PROCESSED
                document.save(update_fields=["status"])
                processed_count += 1

                logger.info(
                    "Document ID %s processed. Chunks: %s",
                    document.id,
                    result["chunk_count"],
                )

            except Exception:
                logger.exception(
                    "Failed to process document ID %s",
                    document.id,
                )
                document.status = Document.Status.ERROR
                document.save(update_fields=["status"])
                failed_count += 1

        if processed_count:
            self.message_user(
                request,
                f"{processed_count} document(s) processed successfully.",
                messages.SUCCESS,
            )

        if failed_count:
            self.message_user(
                request,
                f"{failed_count} document(s) failed. Check server logs.",
                messages.ERROR,
            )

        if skipped_count:
            self.message_user(
                request,
                f"{skipped_count} document(s) skipped due to their status.",
                messages.WARNING,
            )

    @admin.action(description="Reject selected documents")
    def reject_documents(self, request, queryset):
        allowed_statuses = [
            Document.Status.PENDING,
            Document.Status.APPROVED,
            Document.Status.ERROR,
        ]

        updated = queryset.filter(
            status__in=allowed_statuses
        ).update(
            status=Document.Status.REJECTED,
            reviewed_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{updated} document(s) rejected.",
            messages.WARNING,
        )
