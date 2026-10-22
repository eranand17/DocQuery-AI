
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const fileInput = document.querySelector('input[type="file"]');
    const uploadButton = document.querySelector(".upload-button");

    if (!form || !fileInput || !uploadButton) {
        return;
    }

    fileInput.addEventListener("change", function () {
        const file = fileInput.files[0];

        if (!file) {
            return;
        }

        const maxSize = 10 * 1024 * 1024;
        const fileName = file.name.toLowerCase();

        if (!fileName.endsWith(".pdf")) {
            alert("Please select a PDF file only.");
            fileInput.value = "";
            return;
        }

        if (file.size > maxSize) {
            alert("File size must not exceed 10 MB.");
            fileInput.value = "";
        }
    });

    form.addEventListener("submit", function () {
        if (!form.checkValidity()) {
            return;
        }

        uploadButton.disabled = true;
        uploadButton.textContent = "Uploading...";
    });
});
