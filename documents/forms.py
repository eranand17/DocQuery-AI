from django import forms
from pypdf import PdfReader
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if not uploaded_file:
            return uploaded_file

        if not uploaded_file.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are allowed.")

        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "File size must not exceed 10 MB."
            )

        try:
            PdfReader(uploaded_file)
            uploaded_file.seek(0)
        except Exception:
            raise forms.ValidationError(
                "The uploaded file is not a valid PDF."
            )

        return uploaded_file
