export class Toast {
  static container = null;
  static recentToasts = new Map();
  static MAX_TOASTS = 3;

  static init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  }

  static show(message, type = 'info', duration = 3000) {
    this.init();

    // Debounce duplicate messages within 3 seconds
    const now = Date.now();
    const lastSeen = this.recentToasts.get(message);
    if (lastSeen && (now - lastSeen) < 3000) {
      return; // Ignore duplicate toast
    }
    this.recentToasts.set(message, now);

    // Keep map bounded
    if (this.recentToasts.size > 20) {
      const oldestKey = this.recentToasts.keys().next().value;
      this.recentToasts.delete(oldestKey);
    }

    // Limit maximum concurrent toasts on screen to 3
    while (this.container.children.length >= this.MAX_TOASTS) {
      const oldestToast = this.container.firstElementChild;
      if (oldestToast) {
        oldestToast.remove();
      } else {
        break;
      }
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `
      <span style="font-weight: 800; font-size: 1.1rem;">${icon}</span>
      <span>${message}</span>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'toastSlideIn 0.25s reverse ease-in forwards';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  static success(msg) { this.show(msg, 'success'); }
  static error(msg) { this.show(msg, 'error'); }
  static info(msg) { this.show(msg, 'info'); }
}
