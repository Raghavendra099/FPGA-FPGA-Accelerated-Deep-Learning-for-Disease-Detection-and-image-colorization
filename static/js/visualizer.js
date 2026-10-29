/**
 * Multi-Modal Medical Visualizer Controls.
 * Handles tab toggles between Grayscale, Colorized, Grad-CAM, and Segmentation Overlays.
 */
document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".view-tab-btn");
  const layers = document.querySelectorAll(".visualizer-layer");
  const opacitySlider = document.getElementById("overlayOpacitySlider");
  const activeOverlayImg = document.getElementById("activeOverlayImg");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const targetLayerId = tab.getAttribute("data-layer");
      layers.forEach((layer) => {
        if (layer.id === targetLayerId) {
          layer.style.display = "block";
        } else {
          layer.style.display = "none";
        }
      });
    });
  });

  // Opacity slider for overlays
  if (opacitySlider && activeOverlayImg) {
    opacitySlider.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value) / 100.0;
      activeOverlayImg.style.opacity = val;
    });
  }
});
