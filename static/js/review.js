/**
 * Review Viewport Pan & Zoom and Action Handlers.
 */
document.addEventListener("DOMContentLoaded", () => {
  const viewport = document.getElementById("reviewViewport");
  const scanImg = document.getElementById("reviewScanImg");
  const zoomInBtn = document.getElementById("zoomInBtn");
  const zoomOutBtn = document.getElementById("zoomOutBtn");
  const zoomResetBtn = document.getElementById("zoomResetBtn");

  if (!viewport || !scanImg) return;

  let scale = 1.0;
  let panX = 0;
  let panY = 0;
  let isDragging = false;
  let startX = 0;
  let startY = 0;

  function updateTransform() {
    scanImg.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
  }

  if (zoomInBtn) {
    zoomInBtn.addEventListener("click", () => {
      scale = Math.min(4.0, scale + 0.25);
      updateTransform();
    });
  }

  if (zoomOutBtn) {
    zoomOutBtn.addEventListener("click", () => {
      scale = Math.max(0.5, scale - 0.25);
      updateTransform();
    });
  }

  if (zoomResetBtn) {
    zoomResetBtn.addEventListener("click", () => {
      scale = 1.0;
      panX = 0;
      panY = 0;
      updateTransform();
    });
  }

  // Mouse wheel zoom
  viewport.addEventListener("wheel", (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.15 : 0.15;
    scale = Math.max(0.5, Math.min(4.0, scale + delta));
    updateTransform();
  });

  // Mouse drag pan
  viewport.addEventListener("mousedown", (e) => {
    isDragging = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
    viewport.style.cursor = "grabbing";
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
    updateTransform();
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
    viewport.style.cursor = "grab";
  });
});
