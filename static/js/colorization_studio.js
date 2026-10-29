/**
 * Interactive Before-and-After Comparison Slider for Medical Colorization Studio.
 */
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("comparisonSliderContainer");
  const overlay = document.getElementById("comparisonOverlay");
  const handle = document.getElementById("comparisonHandle");

  if (!container || !overlay || !handle) return;

  let isSliding = false;

  function setSliderPosition(clientX) {
    const rect = container.getBoundingClientRect();
    let x = clientX - rect.left;
    x = Math.max(0, Math.min(x, rect.width));
    const percent = (x / rect.width) * 100;

    overlay.style.width = `${percent}%`;
    handle.style.left = `${percent}%`;
  }

  handle.addEventListener("mousedown", () => { isSliding = true; });
  container.addEventListener("mousedown", (e) => {
    isSliding = true;
    setSliderPosition(e.clientX);
  });

  window.addEventListener("mousemove", (e) => {
    if (!isSliding) return;
    setSliderPosition(e.clientX);
  });

  window.addEventListener("mouseup", () => {
    isSliding = false;
  });

  // Touch support for tablets and mobile
  handle.addEventListener("touchstart", () => { isSliding = true; }, { passive: true });
  window.addEventListener("touchmove", (e) => {
    if (!isSliding) return;
    if (e.touches && e.touches[0]) {
      setSliderPosition(e.touches[0].clientX);
    }
  }, { passive: true });
  window.addEventListener("touchend", () => { isSliding = false; });
});
