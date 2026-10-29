/**
 * SmartMed AI - Global Client Application Script
 */
document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar drawer toggle
  const toggleBtn = document.querySelector(".mobile-nav-toggle");
  const sidebar = document.querySelector(".app-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }

  // Auto-dismiss Django success messages after 5 seconds
  const autoAlerts = document.querySelectorAll(".alert-success");
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s ease";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });
});

// Toast notification helper
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `alert alert-${type}`;
  toast.style.position = "fixed";
  toast.style.bottom = "24px";
  toast.style.right = "24px";
  toast.style.zIndex = "9999";
  toast.style.boxShadow = "var(--shadow-lg)";
  toast.style.maxWidth = "380px";
  toast.innerHTML = `<span>${message}</span>`;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.4s ease";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 4500);
}
