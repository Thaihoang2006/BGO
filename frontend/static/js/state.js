export class AppState {
  static currentView = 'home';
  static currentRoom = null;
  static participantToken = sessionStorage.getItem('bgo_token') || null;
  static roomCode = sessionStorage.getItem('bgo_room_code') || null;
  static playerIndex = null;
  static isHost = false;
  static isLocal = false;
  static selectedGame = 'caro';
  static games = [];
  static listeners = [];

  static setSession(roomCode, token, playerIndex = null, isHost = false, isLocal = false) {
    this.roomCode = roomCode;
    this.participantToken = token;
    this.playerIndex = playerIndex;
    this.isHost = isHost;
    this.isLocal = isLocal;

    if (roomCode && token) {
      sessionStorage.setItem('bgo_room_code', roomCode);
      sessionStorage.setItem('bgo_token', token);
      this.updateRoomBadge(roomCode);
    } else {
      sessionStorage.removeItem('bgo_room_code');
      sessionStorage.removeItem('bgo_token');
      this.updateRoomBadge(null);
    }
  }

  static clearSession() {
    this.setSession(null, null, null, false, false);
    this.currentRoom = null;
    this.notify();
  }

  static updateRoomBadge(code) {
    const pill = document.getElementById('current-room-pill');
    const text = document.getElementById('current-room-text');
    if (pill && text) {
      if (code) {
        text.textContent = code;
        pill.style.display = 'flex';
      } else {
        pill.style.display = 'none';
      }
    }
  }

  static setRoom(room) {
    this.currentRoom = room;
    if (room) {
      this.isLocal = room.is_local;
      this.isHost = room.is_viewer_host;
      this.playerIndex = room.viewer_player_index;
      this.updateRoomBadge(room.room_code);
    }
    this.notify();
  }

  static subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  }

  static notify() {
    this.listeners.forEach(cb => {
      try { cb(this); } catch (e) { console.error('Error in state subscriber:', e); }
    });
  }
}
