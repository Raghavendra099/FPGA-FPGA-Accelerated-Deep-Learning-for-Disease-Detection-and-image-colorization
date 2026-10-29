/**
 * Reconnecting WebSocket & Polling Fallback Client for SmartMed AI.
 */
class SmartMedSyncClient {
  constructor(options = {}) {
    this.sessionId = options.sessionId || null;
    this.channelType = options.channelType || "session"; // "session" or "review"
    this.onImageUploaded = options.onImageUploaded || null;
    this.statusElement = options.statusElement || null;
    this.ws = null;
    this.pollInterval = null;
    this.isWsConnected = false;
    this.reconnectAttempts = 0;

    this.init();
  }

  init() {
    this.connectWebSocket();
  }

  getWebSocketUrl() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    if (this.channelType === "session" && this.sessionId) {
      return `${protocol}//${host}/ws/sessions/${this.sessionId}/`;
    }
    return `${protocol}//${host}/ws/reviews/`;
  }

  connectWebSocket() {
    const wsUrl = this.getWebSocketUrl();
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isWsConnected = true;
        this.reconnectAttempts = 0;
        this.stopPollingFallback();
        this.updateStatus("LIVE (WebSocket Connected)", "success");
        // Heartbeat ping every 25 seconds
        this.pingTimer = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: "PING" }));
          }
        }, 25000);
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.handleEvent(payload);
        } catch (e) {
          console.error("Error parsing WebSocket message:", e);
        }
      };

      this.ws.onclose = () => {
        this.isWsConnected = false;
        clearInterval(this.pingTimer);
        this.updateStatus("Syncing via Polling Fallback", "warning");
        this.startPollingFallback();
        // Try reconnecting after 4s
        setTimeout(() => this.connectWebSocket(), 4000);
      };

      this.ws.onerror = (err) => {
        this.isWsConnected = false;
        this.startPollingFallback();
      };
    } catch (e) {
      this.startPollingFallback();
    }
  }

  handleEvent(payload) {
    const eventName = payload.event;
    if (eventName === "IMAGE_UPLOADED" || eventName === "NEW_PENDING_IMAGE") {
      this.updateStatus("Image Received! Redirecting...", "success");
      if (typeof this.onImageUploaded === "function") {
        this.onImageUploaded(payload.data);
      }
    }
  }

  startPollingFallback() {
    if (this.pollInterval || !this.sessionId) return;
    this.pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/uploads/api/sessions/${this.sessionId}/status/`);
        if (res.ok) {
          const data = await res.json();
          if (data.status === "IMAGE_UPLOADED" && data.image_id) {
            this.stopPollingFallback();
            if (typeof this.onImageUploaded === "function") {
              this.onImageUploaded(data);
            }
          }
        }
      } catch (err) {
        // Polling retry
      }
    }, 3000);
  }

  stopPollingFallback() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  updateStatus(text, badgeType = "info") {
    if (this.statusElement) {
      this.statusElement.textContent = text;
      this.statusElement.className = `badge badge-${badgeType}`;
    }
  }
}
