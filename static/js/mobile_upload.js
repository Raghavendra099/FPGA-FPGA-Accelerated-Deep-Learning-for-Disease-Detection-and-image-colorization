/**
 * Mobile-First Upload Logic for SmartMed AI QR Upload.
 */
document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("mobileFileInput");
  const previewBox = document.getElementById("previewBox");
  const previewImg = document.getElementById("previewImg");
  const placeholderText = document.getElementById("placeholderText");
  const fileMetaText = document.getElementById("fileMetaText");
  const uploadBtn = document.getElementById("uploadBtn");
  const removeBtn = document.getElementById("removeBtn");
  const progressContainer = document.getElementById("progressContainer");
  const progressBarFill = document.getElementById("progressBarFill");
  const uploadForm = document.getElementById("mobileUploadForm");
  const errorAlert = document.getElementById("mobileErrorAlert");
  const successCard = document.getElementById("mobileSuccessCard");
  const uploadCard = document.getElementById("mobileUploadCard");

  if (!fileInput) return;

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Client-side format verification
    const validTypes = ["image/jpeg", "image/png", "image/jpg"];
    if (!validTypes.includes(file.type.toLowerCase())) {
      showError("Unsupported format. Please select a JPEG or PNG medical scan.");
      fileInput.value = "";
      return;
    }

    // Client-side size check (25MB limit)
    const maxBytes = 25 * 1024 * 1024;
    if (file.size > maxBytes) {
      showError("File size exceeds 25MB limit. Please choose a smaller scan.");
      fileInput.value = "";
      return;
    }

    hideError();

    // Read and display preview
    const reader = new FileReader();
    reader.onload = (event) => {
      previewImg.src = event.target.result;
      previewImg.style.display = "block";
      if (placeholderText) placeholderText.style.display = "none";
      if (removeBtn) removeBtn.style.display = "inline-flex";
      uploadBtn.disabled = false;

      const sizeKb = (file.size / 1024).toFixed(1);
      fileMetaText.textContent = `${file.name} • ${sizeKb} KB`;
    };
    reader.readAsDataURL(file);
  });

  if (removeBtn) {
    removeBtn.addEventListener("click", () => {
      fileInput.value = "";
      previewImg.src = "";
      previewImg.style.display = "none";
      if (placeholderText) placeholderText.style.display = "block";
      removeBtn.style.display = "none";
      uploadBtn.disabled = true;
      fileMetaText.textContent = "";
      hideError();
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const file = fileInput.files[0];
      if (!file) return;

      const uploadUrl = uploadForm.getAttribute("action");
      const formData = new FormData();
      formData.append("image", file);

      uploadBtn.disabled = true;
      uploadBtn.textContent = "Uploading Image...";
      progressContainer.style.display = "block";
      progressBarFill.style.width = "0%";
      hideError();

      const xhr = new XMLHttpRequest();
      xhr.open("POST", uploadUrl, true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          progressBarFill.style.width = percent + "%";
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            // Show Success Card
            if (uploadCard) uploadCard.style.display = "none";
            if (successCard) {
              successCard.style.display = "block";
              const refSpan = document.getElementById("uploadRefSpan");
              if (refSpan && data.image_id) {
                refSpan.textContent = data.image_id;
              }
            }
          } catch (err) {
            showError("Upload successful, but unexpected server response.");
          }
        } else {
          try {
            const data = JSON.parse(xhr.responseText);
            showError(data.error || "Upload failed. Please try again.");
          } catch (e) {
            showError(`Upload error (HTTP ${xhr.status}).`);
          }
          uploadBtn.disabled = false;
          uploadBtn.textContent = "Upload Image";
          progressContainer.style.display = "none";
        }
      };

      xhr.onerror = () => {
        showError("Network connection error. Check your Wi-Fi/cellular connection.");
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Upload Image";
        progressContainer.style.display = "none";
      };

      xhr.send(formData);
    });
  }

  function showError(msg) {
    if (errorAlert) {
      errorAlert.textContent = msg;
      errorAlert.style.display = "block";
    }
  }

  function hideError() {
    if (errorAlert) {
      errorAlert.style.display = "none";
    }
  }
});
