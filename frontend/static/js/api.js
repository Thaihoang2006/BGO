import { Toast } from './components/toast.js';

export class ApiService {
  static socket = null;
  static listeners = {};

  static initSocket() {
    if (this.socket) return;

    if (typeof io === 'undefined') {
      console.warn('Socket.IO client library not loaded, using REST fallback');
      return;
    }

    this.socket = io(window.location.origin, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 10,
      reconnectionDelay: 1000
    });

    this.socket.on('connect', () => {
      console.log('Socket connected:', this.socket.id);
      this.updateConnectionStatus(true);
      this.trigger('connect', this.socket.id);

      // Check if we need to rejoin a room
      const savedCode = sessionStorage.getItem('bgo_room_code');
      const savedToken = sessionStorage.getItem('bgo_token');
      if (savedCode && savedToken) {
        this.joinRoomSocket(savedCode, savedToken);
      }
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
      this.updateConnectionStatus(false);
      this.trigger('disconnect');
    });

    this.socket.on('room_sync', (data) => this.trigger('room_sync', data));
    this.socket.on('player_connected', (data) => this.trigger('player_connected', data));
    this.socket.on('player_disconnected', (data) => this.trigger('player_disconnected', data));
    this.socket.on('player_ready_changed', (data) => this.trigger('player_ready_changed', data));
    this.socket.on('game_started', (data) => this.trigger('game_started', data));
    this.socket.on('game_update', (data) => this.trigger('game_update', data));
    this.socket.on('game_restarted', (data) => this.trigger('game_restarted', data));
    this.socket.on('rematch_requested', (data) => this.trigger('rematch_requested', data));
    this.socket.on('rematch_declined', (data) => this.trigger('rematch_declined', data));
    this.socket.on('room_game_changed', (data) => this.trigger('room_game_changed', data));
    this.socket.on('player_left', (data) => this.trigger('player_left', data));
    this.socket.on('host_transferred', (data) => this.trigger('host_transferred', data));
    this.socket.on('new_chat_message', (data) => this.trigger('new_chat_message', data));
    this.socket.on('action_error', (data) => {
      Toast.error(data.message || 'Lỗi nước đi');
      this.trigger('action_error', data);
    });
    this.socket.on('error_msg', (data) => {
      Toast.error(data.message || 'Lỗi hệ thống');
      this.trigger('error_msg', data);
    });
  }

  static updateConnectionStatus(isOnline) {
    const dot = document.getElementById('connection-status-dot');
    const text = document.getElementById('connection-status-text');
    if (dot && text) {
      if (isOnline) {
        dot.className = 'status-dot';
        text.textContent = 'Trực tuyến';
      } else {
        dot.className = 'status-dot offline';
        text.textContent = 'Mất kết nối';
      }
    }
  }

  static on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    if (!this.listeners[event].includes(callback)) {
      this.listeners[event].push(callback);
    }
  }

  static off(event, callback) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }

  static removeAllListeners(event) {
    if (event) {
      delete this.listeners[event];
    } else {
      this.listeners = {};
    }
  }

  static trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => {
        try { cb(data); } catch (e) { console.error('Error in event listener:', e); }
      });
    }
  }

  // Socket actions
  static joinRoomSocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('join_room_socket', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static setReadySocket(roomCode, participantToken, isReady) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('set_ready', {
        room_code: roomCode,
        participant_token: participantToken,
        is_ready: isReady
      });
    }
  }

  static startGameSocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('start_game', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static sendActionSocket(roomCode, participantToken, action, clientVersion) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('game_action', {
        room_code: roomCode,
        participant_token: participantToken,
        action: action,
        client_version: clientVersion
      });
    }
  }

  static restartGameSocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('restart_game', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static requestRematchSocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('request_rematch', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static declineRematchSocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('decline_rematch', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static switchGameSocket(roomCode, participantToken, newGameType) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('switch_game', {
        room_code: roomCode,
        participant_token: participantToken,
        new_game_type: newGameType
      });
    }
  }

  static returnToLobbySocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('return_to_lobby', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static leaveRoomSocket(roomCode, participantToken) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('leave_room', {
        room_code: roomCode,
        participant_token: participantToken
      });
    }
  }

  static returnToLobby(roomCode, participantToken) {
    this.returnToLobbySocket(roomCode, participantToken);
  }

  static requestRematch(roomCode, participantToken) {
    this.requestRematchSocket(roomCode, participantToken);
  }

  static sendGameAction(roomCode, participantToken, action, clientVersion) {
    this.sendActionSocket(roomCode, participantToken, action, clientVersion);
  }

  static postGameAction(roomCode, participantToken, action, clientVersion) {
    return this.sendActionRest(roomCode, participantToken, action, clientVersion);
  }

  static transferHostSocket(roomCode, participantToken, newHostPlayerIndex) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('transfer_host', {
        room_code: roomCode,
        participant_token: participantToken,
        new_host_player_index: newHostPlayerIndex
      });
    }
  }

  static updateSettingsSocket(roomCode, participantToken, settings) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('update_settings', {
        room_code: roomCode,
        participant_token: participantToken,
        settings: settings
      });
    }
  }

  // REST endpoints
  static async getGames() {
    const res = await fetch('/api/games');
    return await res.json();
  }

  static async getRules(gameType) {
    const res = await fetch(`/api/games/${gameType}/rules`);
    return await res.json();
  }

  static async createRoom(gameType, playerName, isLocal = false, localPlayers = null, settings = null, maxPlayers = null) {
    const res = await fetch('/api/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_type: gameType,
        player_name: playerName,
        is_local: isLocal,
        local_players: localPlayers,
        settings: settings,
        max_players: maxPlayers
      })
    });
    return await res.json();
  }

  static async joinRoom(roomCode, playerName, role = 'player') {
    const res = await fetch(`/api/rooms/${roomCode}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_name: playerName, role: role })
    });
    return await res.json();
  }

  static async getRoom(roomCode, participantToken = null) {
    const headers = {};
    if (participantToken) headers['X-Participant-Token'] = participantToken;
    const res = await fetch(`/api/rooms/${roomCode}`, { headers });
    return await res.json();
  }

  static async sendActionRest(roomCode, participantToken, action, clientVersion) {
    const res = await fetch(`/api/rooms/${roomCode}/action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Participant-Token': participantToken
      },
      body: JSON.stringify({
        action: action,
        client_version: clientVersion
      })
    });
    return await res.json();
  }

  static async restartGameRest(roomCode, participantToken) {
    const res = await fetch(`/api/rooms/${roomCode}/restart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Participant-Token': participantToken
      }
    });
    return await res.json();
  }

  static async requestRematchRest(roomCode, participantToken) {
    const res = await fetch(`/api/rooms/${roomCode}/rematch/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Participant-Token': participantToken
      }
    });
    return await res.json();
  }

  static async declineRematchRest(roomCode, participantToken) {
    const res = await fetch(`/api/rooms/${roomCode}/rematch/decline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Participant-Token': participantToken
      }
    });
    return await res.json();
  }

  static async switchGameRest(roomCode, participantToken, newGameType) {
    const res = await fetch(`/api/rooms/${roomCode}/switch_game`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Participant-Token': participantToken
      },
      body: JSON.stringify({ new_game_type: newGameType })
    });
    return await res.json();
  }

  static async returnToLobbyRest(roomCode, participantToken) {
    const res = await fetch(`/api/rooms/${roomCode}/return_to_lobby`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Participant-Token': participantToken
      }
    });
    return await res.json();
  }

  static async getChatMessages(roomCode) {
    try {
      const res = await fetch(`/api/rooms/${roomCode}/chat`);
      return await res.json();
    } catch (e) {
      console.error('Failed to get chat messages:', e);
      return { success: false, messages: [] };
    }
  }

  static async sendChatMessage(roomCode, participantToken, message) {
    const cleanMsg = (message || '').trim();
    if (!cleanMsg) return { success: false, error: 'Tin nhắn trống' };

    if (this.socket && this.socket.connected) {
      this.socket.emit('send_chat', {
        room_code: roomCode,
        participant_token: participantToken,
        message: cleanMsg
      });
      return { success: true };
    } else {
      try {
        const res = await fetch(`/api/rooms/${roomCode}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Participant-Token': participantToken
          },
          body: JSON.stringify({ participant_token: participantToken, message: cleanMsg })
        });
        return await res.json();
      } catch (e) {
        console.error('Failed to send chat message:', e);
        return { success: false, error: 'Lỗi gửi tin nhắn' };
      }
    }
  }
}
