import { AppState } from '../state.js';
import { ApiService } from '../api.js';

export class RoomChat {
  static isOpen = false;
  static unreadCount = 0;
  static roomCode = null;
  static participantToken = null;
  static isLocal = false;
  static previewTimeout = null;
  static initialized = false;

  static init() {
    if (this.initialized) return;
    this.initialized = true;

    this.mountDOM();
    this.attachEvents();

    // Subscribe to new incoming chat messages via ApiService
    ApiService.on('new_chat_message', (msg) => {
      this.handleIncomingMessage(msg);
    });

    console.log('💬 RoomChat component initialized');
  }

  static mountDOM() {
    if (document.getElementById('room-chat-widget')) return;

    const widget = document.createElement('div');
    widget.id = 'room-chat-widget';
    widget.className = 'room-chat-widget';
    widget.style.display = 'none';

    widget.innerHTML = `
      <!-- Toast Preview when closed -->
      <div id="chat-preview-toast" class="chat-preview-toast" style="display: none;">
        <div class="chat-preview-sender" id="chat-preview-sender"></div>
        <div class="chat-preview-text" id="chat-preview-text"></div>
      </div>

      <!-- Floating Toggle Pill Button -->
      <button id="btn-toggle-chat" class="btn-chat-toggle" title="Mở phòng trò chuyện">
        <span class="chat-icon">💬</span>
        <span class="chat-toggle-text">Chat Phòng</span>
        <span id="chat-unread-badge" class="chat-unread-badge" style="display: none;">0</span>
      </button>

      <!-- Floating Chat Window / Drawer -->
      <div id="room-chat-drawer" class="room-chat-drawer" style="display: none;">
        <!-- Header -->
        <div class="room-chat-header">
          <div class="chat-header-info">
            <span class="chat-header-icon">💬</span>
            <div class="chat-header-titles">
              <span class="chat-header-title">Trò Chuyện Phòng</span>
              <span class="chat-header-code" id="chat-room-code-badge">BGO...</span>
            </div>
          </div>
          <div class="chat-header-actions">
            <button id="btn-minimize-chat" class="btn-chat-action" title="Thu nhỏ">✕</button>
          </div>
        </div>

        <!-- Messages Scroll Container -->
        <div id="room-chat-messages" class="room-chat-messages">
          <div class="chat-empty-state" id="chat-empty-state">
            <span>Chưa có tin nhắn nào.<br>Hãy gửi lời chào đầu tiên! 👋</span>
          </div>
        </div>

        <!-- Quick Emoji Reactions Bar -->
        <div class="room-chat-quick-emojis">
          <button type="button" class="btn-quick-emoji" data-emoji="👋">👋</button>
          <button type="button" class="btn-quick-emoji" data-emoji="🕵️">🕵️</button>
          <button type="button" class="btn-quick-emoji" data-emoji="🤫">🤫</button>
          <button type="button" class="btn-quick-emoji" data-emoji="🤔">🤔</button>
          <button type="button" class="btn-quick-emoji" data-emoji="👀">👀</button>
          <button type="button" class="btn-quick-emoji" data-emoji="🔥">🔥</button>
          <button type="button" class="btn-quick-emoji" data-emoji="👏">👏</button>
          <button type="button" class="btn-quick-emoji" data-emoji="GG!">GG!</button>
          <button type="button" class="btn-quick-emoji" data-emoji="😱">😱</button>
        </div>

        <!-- Input Form -->
        <form id="room-chat-form" class="room-chat-input-form">
          <input type="text" id="room-chat-input" class="room-chat-input" placeholder="Nhập tin nhắn... (Enter để gửi)" maxlength="250" autocomplete="off" />
          <button type="submit" id="btn-send-chat" class="btn-send-chat" title="Gửi tin nhắn">
            <span>➤</span>
          </button>
        </form>
      </div>
    `;

    document.body.appendChild(widget);
  }

  static attachEvents() {
    const btnToggle = document.getElementById('btn-toggle-chat');
    const btnMinimize = document.getElementById('btn-minimize-chat');
    const form = document.getElementById('room-chat-form');
    const input = document.getElementById('room-chat-input');
    const quickEmojiBtns = document.querySelectorAll('.btn-quick-emoji');

    btnToggle?.addEventListener('click', () => {
      this.toggleDrawer();
    });

    btnMinimize?.addEventListener('click', () => {
      this.closeDrawer();
    });

    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = (input?.value || '').trim();
      if (text) {
        this.sendMessage(text);
        if (input) input.value = '';
        input?.focus();
      }
    });

    quickEmojiBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const emoji = btn.dataset.emoji;
        if (emoji) {
          this.sendMessage(emoji);
        }
      });
    });
  }

  static setRoom(roomCode, participantToken, isLocal = false) {
    this.roomCode = roomCode;
    this.participantToken = participantToken;
    this.isLocal = isLocal;

    const widget = document.getElementById('room-chat-widget');
    const codeBadge = document.getElementById('chat-room-code-badge');

    if (!widget) return;

    if (isLocal || !roomCode) {
      widget.style.display = 'none';
      this.closeDrawer();
      this.clearMessages();
    } else {
      widget.style.display = 'flex';
      if (codeBadge) {
        codeBadge.textContent = roomCode;
      }
      this.loadHistory();
    }
  }

  static showWidget() {
    const widget = document.getElementById('room-chat-widget');
    if (widget && !this.isLocal && this.roomCode) {
      widget.style.display = 'flex';
    }
  }

  static hideWidget() {
    const widget = document.getElementById('room-chat-widget');
    if (widget) {
      widget.style.display = 'none';
    }
    this.closeDrawer();
  }

  static toggleDrawer() {
    if (this.isOpen) {
      this.closeDrawer();
    } else {
      this.openDrawer();
    }
  }

  static openDrawer() {
    this.isOpen = true;
    const drawer = document.getElementById('room-chat-drawer');
    const badge = document.getElementById('chat-unread-badge');
    const toast = document.getElementById('chat-preview-toast');

    if (drawer) drawer.style.display = 'flex';
    if (badge) {
      badge.style.display = 'none';
      badge.textContent = '0';
    }
    if (toast) toast.style.display = 'none';
    this.unreadCount = 0;

    this.scrollToBottom();

    setTimeout(() => {
      document.getElementById('room-chat-input')?.focus();
    }, 100);
  }

  static closeDrawer() {
    this.isOpen = false;
    const drawer = document.getElementById('room-chat-drawer');
    if (drawer) drawer.style.display = 'none';
  }

  static async loadHistory() {
    if (!this.roomCode) return;
    try {
      const res = await ApiService.getChatMessages(this.roomCode);
      if (res.success && Array.isArray(res.messages)) {
        this.clearMessages();
        res.messages.forEach(m => this.appendMessageDOM(m, false));
        this.scrollToBottom();
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
  }

  static clearMessages() {
    const container = document.getElementById('room-chat-messages');
    if (container) {
      container.innerHTML = `
        <div class="chat-empty-state" id="chat-empty-state">
          <span>Chưa có tin nhắn nào.<br>Hãy gửi lời chào đầu tiên! 👋</span>
        </div>
      `;
    }
  }

  static handleIncomingMessage(msg) {
    if (!msg || msg.room_code !== this.roomCode) return;

    this.appendMessageDOM(msg, true);

    if (this.isOpen) {
      this.scrollToBottom();
    } else {
      // Unread notification when chat drawer is closed
      if (msg.msg_type === 'user') {
        this.unreadCount++;
        const badge = document.getElementById('chat-unread-badge');
        if (badge) {
          badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
          badge.style.display = 'flex';
        }

        // Show quick preview toast
        this.showPreviewToast(msg.sender_name, msg.message);
      }
    }
  }

  static showPreviewToast(senderName, text) {
    const toast = document.getElementById('chat-preview-toast');
    const senderEl = document.getElementById('chat-preview-sender');
    const textEl = document.getElementById('chat-preview-text');

    if (!toast || !senderEl || !textEl) return;

    senderEl.textContent = senderName + ':';
    textEl.textContent = text;
    toast.style.display = 'block';

    if (this.previewTimeout) clearTimeout(this.previewTimeout);
    this.previewTimeout = setTimeout(() => {
      toast.style.display = 'none';
    }, 3800);
  }

  static appendMessageDOM(msg, animate = false) {
    const container = document.getElementById('room-chat-messages');
    const emptyState = document.getElementById('chat-empty-state');
    if (!container) return;

    if (emptyState) {
      emptyState.remove();
    }

    const isMe = (msg.player_index !== null && msg.player_index !== undefined && msg.player_index === AppState.playerIndex);
    const msgEl = document.createElement('div');

    let roleBadgeHtml = '';
    if (msg.sender_role === 'spectator') {
      roleBadgeHtml = '<span class="badge-role-spectator">👁️ Khán giả</span>';
    } else if (msg.is_host) {
      roleBadgeHtml = '<span class="badge-role-host">👑 Chủ phòng</span>';
    } else if (msg.msg_type === 'user') {
      roleBadgeHtml = '<span class="badge-role-player">Người chơi</span>';
    }

    if (msg.msg_type === 'system') {
      msgEl.className = 'chat-msg system';
      msgEl.innerHTML = `
        <span class="system-pill">${this.escapeHtml(msg.message)}</span>
      `;
    } else if (isMe) {
      msgEl.className = 'chat-msg me';
      msgEl.innerHTML = `
        <div class="msg-sender-header" style="justify-content: flex-end;">
          ${roleBadgeHtml}
          <span>Bạn</span>
        </div>
        <div class="msg-bubble-me">
          ${this.escapeHtml(msg.message)}
        </div>
        <span class="msg-timestamp">${msg.time || ''}</span>
      `;
    } else {
      msgEl.className = 'chat-msg other';
      const senderColor = msg.color || 'var(--color-sunset-orange)';
      msgEl.innerHTML = `
        <div class="msg-sender-header" style="color: ${senderColor};">
          <span>${this.escapeHtml(msg.sender_name || 'Người chơi')}</span>
          ${roleBadgeHtml}
        </div>
        <div class="msg-bubble-other">
          ${this.escapeHtml(msg.message)}
        </div>
        <span class="msg-timestamp">${msg.time || ''}</span>
      `;
    }

    container.appendChild(msgEl);
  }

  static lastSendTime = 0;

  static async sendMessage(text) {
    if (!this.roomCode || !text) return;
    const now = Date.now();
    if (now - this.lastSendTime < 450) {
      console.warn('Tin nhắn gửi quá nhanh (cooldown)');
      return;
    }
    this.lastSendTime = now;
    try {
      await ApiService.sendChatMessage(this.roomCode, this.participantToken, text);
    } catch (e) {
      console.error('Send chat error:', e);
    }
  }

  static scrollToBottom() {
    const container = document.getElementById('room-chat-messages');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  static escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
