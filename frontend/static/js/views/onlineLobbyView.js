import { AppState } from '../state.js';
import { Router } from '../router.js';
import { Toast } from '../components/toast.js';
import { ApiService } from '../api.js';
import { SwitchGameModal } from '../components/switchGameModal.js';
import { LeaveRoomHelper } from '../components/leaveRoomHelper.js';

export class OnlineLobbyView {
  static currentCleanup = null;

  static async render(container, params = {}) {
    const mode = params.mode;
    const gameId = params.game || AppState.selectedGame || 'caro';
    const roomCodeParam = params.roomCode || '';

    // If explicit mode requested, respect it
    if (mode === 'create') {
      this.renderCreateForm(container, gameId);
      return;
    }

    if (mode === 'join' && (!AppState.participantToken || roomCodeParam !== AppState.roomCode)) {
      this.renderJoinForm(container, roomCodeParam);
      return;
    }

    const targetRoomCode = roomCodeParam || AppState.roomCode;
    // If returning to lobby or has active session
    if (targetRoomCode && AppState.participantToken) {
      try {
        const res = await ApiService.getRoom(targetRoomCode, AppState.participantToken);
        if (res.success && res.room) {
          AppState.setRoom(res.room);
          if (res.room.status === 'waiting') {
            this.renderWaitingLobby(container, res.room);
            return;
          } else if (res.room.status === 'playing') {
            const view = (res.room.game_type === 'gem_kingdom' ? 'gem_kingdom_play' :
                          res.room.game_type === 'ludo' ? 'ludo_play' :
                          res.room.game_type === 'monopoly' ? 'monopoly_play' :
                          res.room.game_type === 'undercover' ? 'undercover_play' : 'caro_play');
            Router.navigate(view, { roomCode: res.room.room_code });
            return;
          }
        }
      } catch (e) {
        console.error('Failed to load room:', e);
      }
    }

    // If already in an active waiting room
    if (AppState.roomCode && AppState.currentRoom && AppState.currentRoom.status === 'waiting') {
      this.renderWaitingLobby(container, AppState.currentRoom);
      return;
    }

    if (roomCodeParam && roomCodeParam !== AppState.roomCode) {
      this.renderJoinForm(container, roomCodeParam);
      return;
    }

    // Default to create form
    this.renderCreateForm(container, gameId);
  }

  static renderCreateForm(container, gameId) {
    const gameTitles = {
      'caro': 'Cờ Caro (Gomoku Freestyle 15x15 - 2 Người)',
      'gem_kingdom': 'Gem Kingdom (Splendor - 2 đến 4 Người)',
      'ludo': 'Cờ Cá Ngựa (Ludo - 2 đến 4 Người)',
      'monopoly': 'Cờ Tỷ Phú (Property Tycoon - 2 đến 4 Người)'
    };
    const gameTitleText = gameTitles[gameId] || 'Cờ Caro (2 Người)';

    container.innerHTML = `
      <div class="lobby-container">
        <div class="lobby-header">
          <button class="btn btn-ghost btn-sm" id="btn-back-select" style="margin-bottom: 1rem;">
            ← Quay Lại
          </button>
          <h2>Tạo Phòng Online Mới</h2>
          <p>Tạo phòng, nhận mã phòng độc quyền và gửi cho bạn bè để cùng tham gia</p>
        </div>

        <div class="glass-panel setup-form-panel">
          <div class="form-group">
            <label>Tên của bạn (Chủ phòng):</label>
            <input type="text" id="host-name-input" class="form-input" placeholder="Nhập biệt danh của bạn" value="Chủ phòng" maxlength="20">
          </div>

          <div class="form-group">
            <label>Trò chơi:</label>
            <div style="font-weight: 700; color: var(--color-sunset-orange); font-size: 1.1rem;">
              ${gameTitleText}
            </div>
          </div>

          <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: space-between; flex-wrap: wrap;">
            <button class="btn btn-secondary" id="btn-switch-to-join">
              Đã có mã phòng? Vào phòng
            </button>
            <button class="btn btn-primary btn-lg" id="btn-submit-create-room">
              <span>✨</span> Tạo Phòng Ngay
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btn-back-select')?.addEventListener('click', () => {
      Router.navigate('home');
    });

    document.getElementById('btn-switch-to-join')?.addEventListener('click', () => {
      this.renderJoinForm(container, '');
    });

    document.getElementById('btn-submit-create-room')?.addEventListener('click', async () => {
      const name = document.getElementById('host-name-input').value.trim() || 'Chủ phòng';
      try {
        const res = await ApiService.createRoom(gameId, name, false);
        if (res.success) {
          AppState.setSession(res.room_code, res.participant_token, res.player_index, true, false);
          AppState.setRoom(res.room);
          ApiService.joinRoomSocket(res.room_code, res.participant_token);
          Toast.success(`Phòng ${res.room_code} đã được tạo!`);
          this.renderWaitingLobby(container, res.room);
        } else {
          Toast.error(res.error || 'Không thể tạo phòng');
        }
      } catch (e) {
        console.error(e);
        Toast.error('Lỗi kết nối máy chủ');
      }
    });
  }

  static renderJoinForm(container, defaultCode = '') {
    container.innerHTML = `
      <div class="lobby-container">
        <div class="lobby-header">
          <button class="btn btn-ghost btn-sm" id="btn-back-select" style="margin-bottom: 1rem;">
            ← Quay Lại
          </button>
          <h2>Tham Gia Phòng Online</h2>
          <p>Nhập mã phòng được chia sẻ từ bạn bè để bước vào sảnh chờ</p>
        </div>

        <div class="glass-panel setup-form-panel">
          <div class="form-group">
            <label>Mã phòng (Code):</label>
            <input type="text" id="join-room-code-input" class="form-input" placeholder="Ví dụ: BGO742" value="${defaultCode}" maxlength="8" style="text-transform: uppercase; font-family: monospace; font-size: 1.25rem; letter-spacing: 2px;">
          </div>

          <div class="form-group">
            <label>Tên của bạn:</label>
            <input type="text" id="join-player-name-input" class="form-input" placeholder="Nhập biệt danh của bạn" value="Người chơi" maxlength="20">
          </div>

          <div class="form-group">
            <label>Vai trò tham gia:</label>
            <div style="display: flex; gap: 1rem; margin-top: 0.35rem; flex-wrap: wrap;">
              <label style="display: flex; align-items: center; gap: 0.4rem; cursor: pointer; color: var(--color-cream); font-weight: 600;">
                <input type="radio" name="join-role-choice" value="player" checked>
                <span>🎮 Người chơi chính thức</span>
              </label>
              <label style="display: flex; align-items: center; gap: 0.4rem; cursor: pointer; color: #A0AEC0; font-weight: 600;">
                <input type="radio" name="join-role-choice" value="spectator">
                <span>👁️ Khán giả (Chỉ theo dõi)</span>
              </label>
            </div>
          </div>

          <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: space-between; flex-wrap: wrap;">
            <button class="btn btn-secondary" id="btn-switch-to-create">
              Tạo phòng mới
            </button>
            <button class="btn btn-primary btn-lg" id="btn-submit-join-room">
              <span>🚀</span> Vào Phòng
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btn-back-select')?.addEventListener('click', () => {
      Router.navigate('home');
    });

    document.getElementById('btn-switch-to-create')?.addEventListener('click', () => {
      this.renderCreateForm(container, 'caro');
    });

    document.getElementById('btn-submit-join-room')?.addEventListener('click', async () => {
      const code = document.getElementById('join-room-code-input').value.trim().toUpperCase();
      const name = document.getElementById('join-player-name-input').value.trim() || 'Người chơi';
      const roleChoice = document.querySelector('input[name="join-role-choice"]:checked')?.value || 'player';

      if (!code) {
        Toast.error('Vui lòng nhập mã phòng');
        return;
      }

      try {
        let res = await ApiService.joinRoom(code, name, roleChoice);
        if (!res.success && res.error && res.error.includes('Khán giả')) {
          if (confirm(res.error + '\n\nBấm OK để tham gia ngay với vai trò Khán giả.')) {
            res = await ApiService.joinRoom(code, name, 'spectator');
          }
        }

        if (res.success) {
          AppState.setSession(res.room_code, res.participant_token, res.player_index, false, false);
          AppState.setRoom(res.room);
          ApiService.joinRoomSocket(res.room_code, res.participant_token);
          Toast.success(`Đã vào phòng ${res.room_code}!`);
          this.renderWaitingLobby(container, res.room);
        } else {
          Toast.error(res.error || 'Không thể vào phòng');
        }
      } catch (e) {
        console.error(e);
        Toast.error('Lỗi khi tham gia phòng');
      }
    });
  }

  static renderWaitingLobby(container, room) {
    if (this.currentCleanup) {
      this.currentCleanup();
      this.currentCleanup = null;
    }

    const players = room.players || [];
    // Match my player using is_you, participant_token, or player_index
    let myPlayer = players.find(p => p.is_you);
    if (!myPlayer && AppState.participantToken) {
      myPlayer = players.find(p => p.participant_token === AppState.participantToken);
    }
    if (!myPlayer && AppState.playerIndex !== null && AppState.playerIndex !== undefined) {
      myPlayer = players.find(p => p.player_index === AppState.playerIndex);
    }

    // Determine host status: If myPlayer is host OR AppState.isHost was true OR room says so
    const isHost = (myPlayer && myPlayer.is_host) || AppState.isHost || room.is_viewer_host || false;
    AppState.isHost = isHost;
    if (myPlayer) {
      AppState.playerIndex = myPlayer.player_index;
    }

    const isReady = myPlayer ? myPlayer.is_ready : false;
    const isSpectator = myPlayer ? Boolean(myPlayer.is_spectator) : Boolean(room.is_viewer_spectator);
    const hasEnoughPlayers = players.length >= room.min_players;
    const allNonHostsReady = players.filter(p => !p.is_host).every(p => p.is_ready);
    const canStart = isHost && hasEnoughPlayers && allNonHostsReady;

    const inviteLink = `${window.location.origin}/#online_lobby?roomCode=${room.room_code}&mode=join`;

    container.innerHTML = `
      <div class="lobby-container">
        <div class="lobby-header">
          <h2>Sảnh Chờ Online</h2>
          <div style="font-weight: 700; color: var(--color-sunset-orange); font-size: 1.15rem; margin-top: 0.25rem;">
            🎮 Trò chơi: ${room.game_type === 'gem_kingdom' ? 'Gem Kingdom (Splendor)' : room.game_type === 'ludo' ? 'Cờ Cá Ngựa (Ludo)' : room.game_type === 'monopoly' ? 'Cờ Tỷ Phú (Property Tycoon)' : room.game_type === 'undercover' ? 'Undercover (Ai Là Gián Điệp?)' : 'Cờ Caro (Gomoku)'}
          </div>
          <p style="margin-top: 0.25rem;">Chia sẻ mã phòng hoặc link mời bên dưới cho bạn bè cùng tham gia</p>
        </div>

        <!-- Room Code Display -->
        <div class="room-code-display">
          <span>Mã Phòng Của Bạn</span>
          <div class="room-code-number" id="lobby-code-val">${room.room_code}</div>
          <div style="display: flex; gap: 0.75rem; justify-content: center; margin-top: 1rem; flex-wrap: wrap;">
            <button class="btn btn-secondary btn-sm" id="btn-copy-code">
              📋 Sao Chép Mã Phòng
            </button>
            <button class="btn btn-sunset btn-sm" id="btn-copy-link">
              🔗 Sao Chép Link Tham Gia
            </button>
          </div>
        </div>

        <!-- Instructions Box -->
        <div class="glass-card" style="padding: 1rem 1.25rem; margin-bottom: 1.5rem; font-size: 0.88rem; border-color: rgba(255, 153, 102, 0.3);">
          <strong style="color: var(--color-sunset-orange);">📌 Cách mời người chơi:</strong>
          <span style="color: var(--color-cream-soft); display: block; margin-top: 0.25rem;">
            Gửi mã <strong>${room.room_code}</strong> hoặc link tham gia cho bạn bè (hoặc mở 1 tab ẩn danh trên máy này). Khi người chơi thứ hai bấm <strong>Sẵn sàng</strong>, chủ phòng sẽ có thể bấm <strong>Bắt Đầu Ván Đấu</strong>.
          </span>
        </div>

        <!-- Players List in Lobby -->
        <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 2rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.5rem;">
            <h3 style="font-size: 1.15rem; color: var(--color-cream); font-weight: 700;">
              Người chơi trong phòng (${players.length}/${room.max_players})
            </h3>
            <span style="font-size: 0.82rem; color: var(--color-dusty-rose);">
              Cần đủ ${room.min_players} người để bắt đầu
            </span>
          </div>

          <div class="lobby-players-list">
            ${players.map(p => {
              const isThisPlayerMe = p.is_you || (myPlayer && p.player_index === myPlayer.player_index);
              return `
                <div class="lobby-player-card">
                  <div class="player-info-left">
                    <div class="player-avatar-badge" style="background: ${p.color}; color: #251620;">
                      ${p.symbol}
                    </div>
                    <div class="player-name-wrapper">
                      <h4>
                        ${p.name}
                        ${p.is_host ? '<span class="host-tag">👑 Chủ phòng</span>' : ''}
                        ${isThisPlayerMe ? '<span class="you-tag">Bạn</span>' : ''}
                      </h4>
                      <span style="font-size: 0.78rem; color: var(--color-dusty-rose);">
                        ${p.is_connected ? '🟢 Trực tuyến' : '🔴 Mất kết nối'}
                      </span>
                    </div>
                  </div>

                  <div>
                    ${p.is_host 
                      ? '<span class="player-status-badge status-ready">Chủ phòng</span>'
                      : (p.is_ready 
                          ? '<span class="player-status-badge status-ready">✓ Đã Sẵn Sàng</span>'
                          : '<span class="player-status-badge status-waiting">⏳ Chưa sẵn sàng</span>'
                        )
                    }
                  </div>
                </div>
              `;
            }).join('')}

            ${players.length < room.max_players ? `
              <div class="lobby-empty-slot">
                <span>Đang đợi thêm người chơi tham gia (${players.length}/${room.max_players})...</span>
              </div>
            ` : ''}

            ${room.spectators && room.spectators.length > 0 ? `
              <div style="margin-top: 1rem; padding: 0.85rem 1.25rem; background: rgba(0, 0, 0, 0.25); border-radius: var(--radius-md); border: 1px dashed rgba(160, 174, 192, 0.4);">
                <div style="font-weight: 700; color: #CBD5E0; margin-bottom: 0.35rem; font-size: 0.88rem;">
                  👁️ Khán giả đang theo dõi (${room.spectators.length}):
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  ${room.spectators.map(s => `<span class="badge-role-spectator">👁️ ${s.name}</span>`).join('')}
                </div>
              </div>
            ` : ''}

            ${isHost && room.game_type === 'undercover' ? `
              <div class="glass-card" style="padding: 1.25rem; margin-top: 1.25rem; border: 1px solid rgba(255, 153, 102, 0.35);">
                <h4 style="color: var(--color-sunset-orange); margin-bottom: 0.75rem; font-size: 1rem;">
                  ⚙️ Cài Đặt Trận Đấu Undercover:
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
                  <div>
                    <label style="font-size: 0.8rem; color: var(--color-dusty-rose); display: block;">Chủ đề từ vựng:</label>
                    <select id="lobby-uc-topic" class="form-input" style="padding: 0.4rem; font-size: 0.85rem;">
                      <option value="all" ${room.settings?.topic === 'all' || !room.settings?.topic ? 'selected' : ''}>Tất cả chủ đề (Ngẫu nhiên)</option>
                      <option value="food" ${room.settings?.topic === 'food' ? 'selected' : ''}>Đồ ăn & Thức uống</option>
                      <option value="animals" ${room.settings?.topic === 'animals' ? 'selected' : ''}>Động vật</option>
                      <option value="vehicles" ${room.settings?.topic === 'vehicles' ? 'selected' : ''}>Phương tiện giao thông</option>
                      <option value="technology" ${room.settings?.topic === 'technology' ? 'selected' : ''}>Công nghệ & Thiết bị</option>
                      <option value="places" ${room.settings?.topic === 'places' ? 'selected' : ''}>Địa điểm & Thiên nhiên</option>
                      <option value="sports" ${room.settings?.topic === 'sports' ? 'selected' : ''}>Thể thao & Trò chơi</option>
                      <option value="daily_life" ${room.settings?.topic === 'daily_life' ? 'selected' : ''}>Đời sống & Gia đình</option>
                    </select>
                  </div>
                  <div>
                    <label style="font-size: 0.8rem; color: var(--color-dusty-rose); display: block;">Số Mũ Đen (Undercover):</label>
                    <input type="number" id="lobby-uc-undercover-cnt" class="form-input" min="1" max="5" value="${room.settings?.undercover_count || 1}" style="padding: 0.4rem;">
                  </div>
                  <div>
                    <label style="font-size: 0.8rem; color: var(--color-dusty-rose); display: block;">Số Mũ Trắng (Mr. White):</label>
                    <input type="number" id="lobby-uc-mrwhite-cnt" class="form-input" min="0" max="3" value="${room.settings?.mrwhite_count !== undefined ? room.settings.mrwhite_count : 1}" style="padding: 0.4rem;">
                  </div>
                  <div>
                    <label style="font-size: 0.8rem; color: var(--color-dusty-rose); display: block;">Thời gian mô tả (giây):</label>
                    <input type="number" id="lobby-uc-desc-time" class="form-input" min="20" max="120" value="${room.settings?.describe_time || 60}" style="padding: 0.4rem;">
                  </div>
                  <div>
                    <label style="font-size: 0.8rem; color: var(--color-dusty-rose); display: block;">Thời gian bỏ phiếu (giây):</label>
                    <input type="number" id="lobby-uc-vote-time" class="form-input" min="15" max="90" value="${room.settings?.vote_time || 45}" style="padding: 0.4rem;">
                  </div>
                  <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem;">
                    <input type="checkbox" id="lobby-uc-mute-spec" ${room.settings?.mute_spectator_chat ? 'checked' : ''}>
                    <label for="lobby-uc-mute-spec" style="font-size: 0.85rem; color: var(--color-cream); cursor: pointer;">Khóa chat khán giả</label>
                  </div>
                </div>
                <button id="btn-save-uc-settings" class="btn btn-sunset btn-sm" style="margin-top: 1rem;">
                  💾 Lưu Thiết Lập Phòng
                </button>
              </div>
            ` : ''}
          </div>

          <!-- Lobby Action Buttons -->
          <div class="lobby-actions">
            <button class="btn btn-danger btn-sm" id="btn-leave-room">
              Rời Phòng
            </button>

            <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
              ${isHost ? `
                <button class="btn btn-secondary btn-lg" id="btn-host-switch-game">
                  🎮 Đổi Trò Chơi
                </button>
              ` : ''}

              ${isSpectator ? `
                <div class="badge-role-spectator" style="font-size: 0.92rem; padding: 0.5rem 1rem;">
                  👁️ Bạn đang là Khán Giả (Đang theo dõi sảnh chờ)
                </div>
              ` : (
                !isHost ? `
                  <button class="btn ${isReady ? 'btn-secondary' : 'btn-sunset'} btn-lg" id="btn-toggle-ready">
                    ${isReady ? '✕ Hủy Sẵn Sàng' : '✓ Tôi Đã Sẵn Sàng!'}
                  </button>
                ` : `
                  <button class="btn btn-primary btn-lg" id="btn-host-start" ${!canStart ? 'disabled style="opacity: 0.55; cursor: not-allowed;"' : ''} title="${!hasEnoughPlayers ? 'Cần đủ số người chơi tối thiểu để bắt đầu' : (!allNonHostsReady ? 'Đang đợi người chơi khác bấm Sẵn sàng' : 'Bấm để bắt đầu ván đấu')}">
                    <span>🎲</span> Bắt Đầu Ván Đấu
                  </button>
                `
              )}
            </div>
          </div>
        </div>

        <!-- In-Lobby Chat Section -->
        <div class="glass-panel" style="padding: 1.25rem 1.5rem; margin-bottom: 2rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
            <h3 style="font-size: 1.15rem; color: var(--color-cream); font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
              <span>💬</span> Trò Chuyện Trong Phòng
            </h3>
            <span style="font-size: 0.8rem; color: var(--color-dusty-rose);">Gửi tin nhắn trực tiếp cho mọi người</span>
          </div>

          <!-- Messages display area -->
          <div id="lobby-chat-messages" style="height: 190px; overflow-y: auto; background: rgba(25, 14, 21, 0.65); border: 1px solid var(--surface-glass-border); border-radius: 12px; padding: 0.75rem 1rem; display: flex; flex-direction: column; gap: 0.55rem; margin-bottom: 0.75rem; scroll-behavior: smooth;">
            <div id="lobby-chat-empty" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-dusty-rose); font-size: 0.85rem; font-style: italic;">
              Chưa có tin nhắn nào. Hãy gửi lời chào đầu tiên! 👋
            </div>
          </div>

          <!-- Quick reactions -->
          <div style="display: flex; gap: 0.4rem; margin-bottom: 0.6rem; overflow-x: auto;">
            <button type="button" class="btn btn-ghost btn-sm btn-lobby-emoji" data-emoji="👋" style="padding: 0.2rem 0.6rem; font-size: 0.88rem; border-radius: 99px;">👋 Chào</button>
            <button type="button" class="btn btn-ghost btn-sm btn-lobby-emoji" data-emoji="🎲" style="padding: 0.2rem 0.6rem; font-size: 0.88rem; border-radius: 99px;">🎲 Sẵn sàng chưa?</button>
            <button type="button" class="btn btn-ghost btn-sm btn-lobby-emoji" data-emoji="🔥" style="padding: 0.2rem 0.6rem; font-size: 0.88rem; border-radius: 99px;">🔥 Chiến thôi</button>
            <button type="button" class="btn btn-ghost btn-sm btn-lobby-emoji" data-emoji="👏" style="padding: 0.2rem 0.6rem; font-size: 0.88rem; border-radius: 99px;">👏 Vỗ tay</button>
            <button type="button" class="btn btn-ghost btn-sm btn-lobby-emoji" data-emoji="GG!" style="padding: 0.2rem 0.6rem; font-size: 0.88rem; border-radius: 99px;">GG!</button>
            <button type="button" class="btn btn-ghost btn-sm btn-lobby-emoji" data-emoji="😎" style="padding: 0.2rem 0.6rem; font-size: 0.88rem; border-radius: 99px;">😎 Căng đấy</button>
          </div>

          <!-- Chat Input -->
          <form id="lobby-chat-form" style="display: flex; gap: 0.6rem;">
            <input type="text" id="lobby-chat-input" class="form-input" placeholder="Nhập tin nhắn... (Enter để gửi)" maxlength="250" autocomplete="off" style="flex: 1; padding: 0.6rem 1rem; border-radius: var(--radius-full);">
            <button type="submit" class="btn btn-primary" style="padding: 0.6rem 1.25rem; border-radius: var(--radius-full); display: flex; align-items: center; gap: 0.4rem;">
              <span>➤</span> Gửi
            </button>
          </form>
        </div>
      </div>
    `;

    this.attachWaitingLobbyEvents(container, room, inviteLink);
  }

  static cleanup() {
    if (this.currentCleanup) {
      this.currentCleanup();
      this.currentCleanup = null;
    }
  }

  static attachWaitingLobbyEvents(container, room, inviteLink) {
    this.cleanup();

    document.getElementById('btn-copy-code')?.addEventListener('click', () => {
      navigator.clipboard.writeText(room.room_code).then(() => {
        Toast.success(`Đã sao chép mã phòng: ${room.room_code}`);
      }).catch(() => {
        Toast.info(`Mã phòng: ${room.room_code}`);
      });
    });

    document.getElementById('btn-copy-link')?.addEventListener('click', () => {
      navigator.clipboard.writeText(inviteLink).then(() => {
        Toast.success('Đã sao chép link tham gia phòng!');
      }).catch(() => {
        Toast.info(`Link mời: ${inviteLink}`);
      });
    });

    document.getElementById('btn-leave-room')?.addEventListener('click', () => {
      const isHost = AppState.isHost || room.is_viewer_host;
      LeaveRoomHelper.promptLeave(room.room_code, AppState.participantToken, isHost, false);
    });

    document.getElementById('btn-host-switch-game')?.addEventListener('click', () => {
      SwitchGameModal.open(room.room_code, AppState.participantToken);
    });

    document.getElementById('btn-toggle-ready')?.addEventListener('click', () => {
      const pList = room.players || [];
      const me = pList.find(p => p.is_you || p.player_index === AppState.playerIndex);
      const newReady = me ? !me.is_ready : true;
      ApiService.setReadySocket(room.room_code, AppState.participantToken, newReady);
    });

    document.getElementById('btn-host-start')?.addEventListener('click', () => {
      ApiService.startGameSocket(room.room_code, AppState.participantToken);
    });

    document.getElementById('btn-save-uc-settings')?.addEventListener('click', () => {
      const topic = document.getElementById('lobby-uc-topic')?.value || 'all';
      const ucCnt = parseInt(document.getElementById('lobby-uc-undercover-cnt')?.value) || 1;
      const mwCnt = parseInt(document.getElementById('lobby-uc-mrwhite-cnt')?.value) ?? 1;
      const descTime = parseInt(document.getElementById('lobby-uc-desc-time')?.value) || 60;
      const voteTime = parseInt(document.getElementById('lobby-uc-vote-time')?.value) || 45;
      const muteSpec = document.getElementById('lobby-uc-mute-spec')?.checked || false;

      ApiService.updateSettingsSocket(room.room_code, AppState.participantToken, {
        topic,
        undercover_count: ucCnt,
        mrwhite_count: mwCnt,
        describe_time: descTime,
        vote_time: voteTime,
        mute_spectator_chat: muteSpec
      });
      Toast.success('Đã lưu cấu hình Undercover!');
    });

    // In-Lobby Chat Events
    this.loadLobbyChat(room.room_code);

    const chatForm = document.getElementById('lobby-chat-form');
    const chatInput = document.getElementById('lobby-chat-input');
    chatForm?.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = (chatInput?.value || '').trim();
      if (text) {
        ApiService.sendChatMessage(room.room_code, AppState.participantToken, text);
        if (chatInput) chatInput.value = '';
        chatInput?.focus();
      }
    });

    document.querySelectorAll('.btn-lobby-emoji').forEach(btn => {
      btn.addEventListener('click', () => {
        const emoji = btn.dataset.emoji;
        if (emoji) {
          ApiService.sendChatMessage(room.room_code, AppState.participantToken, emoji);
        }
      });
    });

    const onLobbyChatMessage = (msg) => {
      if (msg.room_code === room.room_code) {
        this.appendLobbyChatMessage(msg);
      }
    };
    ApiService.on('new_chat_message', onLobbyChatMessage);

    // Helper to get view route from game type
    const getViewForGame = (gameType) => {
      if (gameType === 'gem_kingdom') return 'gem_kingdom_play';
      if (gameType === 'ludo') return 'ludo_play';
      if (gameType === 'monopoly') return 'monopoly_play';
      if (gameType === 'undercover') return 'undercover_play';
      return 'caro_play';
    };

    // Socket event handlers
    const onRoomSync = (updatedRoom) => {
      if (AppState.isHost) updatedRoom.is_viewer_host = true;
      AppState.setRoom(updatedRoom);
      if (updatedRoom.status === 'playing') {
        const view = getViewForGame(updatedRoom.game_type);
        Router.navigate(view, { roomCode: updatedRoom.room_code });
      } else {
        this.renderWaitingLobby(container, updatedRoom);
      }
    };

    const onPlayerReady = (data) => {
      if (data.room) {
        if (AppState.isHost) data.room.is_viewer_host = true;
        AppState.setRoom(data.room);
        this.renderWaitingLobby(container, data.room);
      }
    };

    const onRoomGameChanged = (data) => {
      Toast.info(`Chủ phòng đã đổi trò chơi sang: ${data.new_game_type}`);
      if (data.room) {
        if (AppState.isHost) data.room.is_viewer_host = true;
        AppState.setRoom(data.room);
        this.renderWaitingLobby(container, data.room);
      }
    };

    const onGameStarted = (data) => {
      Toast.success('Ván đấu bắt đầu!');
      const gameType = data.game_type || AppState.currentRoom?.game_type || 'caro';
      const view = getViewForGame(gameType);
      Router.navigate(view, { roomCode: data.room_code });
    };

    const onRoomReturnedToLobby = (data) => {
      Toast.info(`${data.requested_by || 'Chủ phòng'} đã đưa phòng về sảnh chờ.`);
      if (data.room) {
        if (AppState.isHost) data.room.is_viewer_host = true;
        AppState.setRoom(data.room);
        this.renderWaitingLobby(container, data.room);
      }
    };

    ApiService.on('room_sync', onRoomSync);
    ApiService.on('player_ready_changed', onPlayerReady);
    ApiService.on('room_game_changed', onRoomGameChanged);
    ApiService.on('room_returned_to_lobby', onRoomReturnedToLobby);
    ApiService.on('game_started', onGameStarted);

    this.currentCleanup = () => {
      ApiService.off('room_sync', onRoomSync);
      ApiService.off('player_ready_changed', onPlayerReady);
      ApiService.off('room_game_changed', onRoomGameChanged);
      ApiService.off('room_returned_to_lobby', onRoomReturnedToLobby);
      ApiService.off('game_started', onGameStarted);
      ApiService.off('new_chat_message', onLobbyChatMessage);
    };
  }

  static async loadLobbyChat(roomCode) {
    const chatContainer = document.getElementById('lobby-chat-messages');
    if (!chatContainer) return;
    try {
      const res = await ApiService.getChatMessages(roomCode);
      if (res.success && Array.isArray(res.messages)) {
        chatContainer.innerHTML = '';
        if (res.messages.length === 0) {
          chatContainer.innerHTML = `
            <div id="lobby-chat-empty" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-dusty-rose); font-size: 0.85rem; font-style: italic;">
              Chưa có tin nhắn nào. Hãy gửi lời chào đầu tiên! 👋
            </div>
          `;
        } else {
          res.messages.forEach(m => this.appendLobbyChatMessage(m));
        }
      }
    } catch (e) {
      console.error('Failed to load lobby chat:', e);
    }
  }

  static appendLobbyChatMessage(msg) {
    const chatContainer = document.getElementById('lobby-chat-messages');
    const emptyEl = document.getElementById('lobby-chat-empty');
    if (!chatContainer) return;

    if (emptyEl) emptyEl.remove();

    const isMe = (msg.player_index !== null && msg.player_index !== undefined && msg.player_index === AppState.playerIndex);
    const msgEl = document.createElement('div');

    if (msg.msg_type === 'system') {
      msgEl.className = 'chat-msg system';
      msgEl.innerHTML = `<span class="system-pill">${this.escapeHtml(msg.message)}</span>`;
    } else if (isMe) {
      msgEl.className = 'chat-msg me';
      msgEl.innerHTML = `
        <div class="msg-bubble-me">${this.escapeHtml(msg.message)}</div>
        <span class="msg-timestamp">${msg.time || ''}</span>
      `;
    } else {
      msgEl.className = 'chat-msg other';
      const senderColor = msg.color || 'var(--color-sunset-orange)';
      msgEl.innerHTML = `
        <div class="msg-sender-header" style="color: ${senderColor};">
          <span>${this.escapeHtml(msg.sender_name || 'Người chơi')}</span>
          ${msg.is_host ? '<span style="font-size: 0.65rem;">👑</span>' : ''}
        </div>
        <div class="msg-bubble-other">${this.escapeHtml(msg.message)}</div>
        <span class="msg-timestamp">${msg.time || ''}</span>
      `;
    }

    chatContainer.appendChild(msgEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;
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
