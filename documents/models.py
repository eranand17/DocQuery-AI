from django.conf import settings
from django.db import models
class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        ERROR = "error", "Error"
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="pdfs/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    results = models.JSONField(null=True, blank=True)
    def __str__(self):
        return self.title
