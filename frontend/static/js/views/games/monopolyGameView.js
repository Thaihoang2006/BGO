import { AppState } from '../../state.js';
import { Router } from '../../router.js';
import { Toast } from '../../components/toast.js';
import { Modal } from '../../components/modal.js';
import { ApiService } from '../../api.js';
import { SwitchGameModal } from '../../components/switchGameModal.js';
import { RematchModal } from '../../components/rematchModal.js';
import { LeaveRoomHelper } from '../../components/leaveRoomHelper.js';

// Pre-computed grid coordinates for the 24 tiles on a 7x7 perimeter
const MONOPOLY_COORDS = [
  // Bottom row (left to right)
  [7, 1], [7, 2], [7, 3], [7, 4], [7, 5], [7, 6], [7, 7],
  // Right column (going up)
  [6, 7], [5, 7], [4, 7], [3, 7], [2, 7], [1, 7],
  // Top row (going left)
  [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1],
  // Left column (going down)
  [2, 1], [3, 1], [4, 1], [5, 1], [6, 1]
];

const DICE_FACES = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];

export class MonopolyGameView {
  static currentCleanup = null;
  static gameState = null;
  static stateVersion = 0;
  static isLocal = false;
  static roomCode = null;

  static async render(container, params = {}) {
    const roomCode = params.roomCode || AppState.roomCode;
    if (!roomCode) {
      Router.navigate('home');
      return;
    }

    this.roomCode = roomCode;

    try {
      const res = await ApiService.getRoom(roomCode, AppState.participantToken);
      if (!res.room) {
        Toast.error('Không tìm thấy phòng chơi');
        Router.navigate('home');
        return;
      }
      AppState.setRoom(res.room);
      this.isLocal = res.room.is_local;
      this.gameState = res.room.game_state;
      this.stateVersion = res.room.state_version;
    } catch (e) {
      console.error(e);
      Toast.error('Không thể tải bàn chơi');
      return;
    }

    if (!this.isLocal) {
      ApiService.joinRoomSocket(roomCode, AppState.participantToken);
    }

    container.innerHTML = `
      <div class="monopoly-container">
        <!-- Match Header -->
        <div class="glass-panel match-header">
          <div class="match-room-info">
            <span class="match-game-title">Cờ Tỷ Phú (Property Tycoon)</span>
            <span class="match-mode-badge">${this.isLocal ? '💻 Local (1 Máy)' : `🌐 Phòng: ${roomCode}`}</span>
          </div>

          <div class="match-controls">
            <button class="btn btn-secondary btn-sm" id="btn-mono-rules">📖 Luật Chơi</button>
            <button class="btn btn-secondary btn-sm" id="btn-mono-switch">🎮 Đổi Trò</button>
            <button class="btn btn-sunset btn-sm" id="btn-mono-room">🏠 Về Phòng</button>
            <button class="btn btn-ghost btn-sm" id="btn-mono-leave">🚪 Rời Bàn</button>
          </div>
        </div>

        <!-- Turn Banner -->
        <div class="turn-banner" id="mono-turn-banner">
          <div class="turn-indicator-dot" id="mono-turn-dot"></div>
          <div class="turn-text" id="mono-turn-text">Đang tải bàn cờ...</div>
        </div>

        <!-- Main Layout -->
        <div class="monopoly-layout">
          <div class="monopoly-board-wrapper">
            <div class="monopoly-board" id="monopoly-board">
              <!-- Tiles and Center rendered dynamically -->
            </div>
          </div>

          <!-- Sidebar -->
          <div class="monopoly-sidebar">
            <div class="glass-panel" style="padding: 1rem;">
              <h4 style="color: var(--color-cream); margin-bottom: 0.75rem; font-size: 0.95rem;">
                💰 Tài Chính & Bất Động Sản
              </h4>
              <div id="mono-players-list" style="display: flex; flex-direction: column; gap: 0.6rem;"></div>
            </div>

            <!-- Manage Owned Properties / Build House -->
            <div class="glass-panel" style="padding: 1rem;" id="mono-my-properties-box">
              <h4 style="color: var(--color-cream); margin-bottom: 0.5rem; font-size: 0.9rem;">
                🔨 Xây Nhà Trên Đất Của Bạn
              </h4>
              <div id="mono-buildable-list" style="display: flex; flex-direction: column; gap: 0.4rem;"></div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.renderGame();
    this.attachEvents();
  }

  static renderGame() {
    if (!this.gameState) return;
    this.renderBoard();
    this.updateHUD();
  }

  static isMyTurn() {
    if (!this.gameState || this.gameState.status !== 'playing') return false;
    if (this.isLocal) return true;
    return AppState.playerIndex === this.gameState.current_player;
  }

  static renderBoard() {
    const boardEl = document.getElementById('monopoly-board');
    if (!boardEl || !this.gameState) return;

    boardEl.innerHTML = '';

    // 1. Center Area with Dice & Action Controls
    const centerEl = document.createElement('div');
    centerEl.className = 'monopoly-center';

    const dice = this.gameState.dice || [1, 1];
    const phase = this.gameState.phase;
    const isMine = this.isMyTurn();
    const currP = this.gameState.players[this.gameState.current_player];

    centerEl.innerHTML = `
      <div class="center-logo">TYCOON</div>
      <div class="dice-pair-display">
        <div class="monopoly-die">${DICE_FACES[dice[0]] || '⚀'}</div>
        <div class="monopoly-die">${DICE_FACES[dice[1]] || '⚀'}</div>
      </div>

      <p style="font-size: 0.8rem; color: var(--color-cream-soft); margin-bottom: 0.8rem; min-height: 2.2em;">
        ${this.gameState.last_log || ''}
      </p>

      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center;">
        ${phase === 'roll' ? `
          <button class="btn btn-primary btn-md" id="btn-mono-roll" ${!isMine ? 'disabled' : ''}>
            🎲 Gieo Xúc Xắc
          </button>
          ${currP.in_jail ? `
            <button class="btn btn-warning btn-md" id="btn-mono-pay-jail" ${!isMine ? 'disabled' : ''}>
              💵 Nộp $50 Ra Tù
            </button>
          ` : ''}
        ` : ''}

        ${phase === 'decision' ? `
          <button class="btn btn-sunset btn-md" id="btn-mono-buy" ${!isMine ? 'disabled' : ''}>
            🏠 Mua Khu Đất Này
          </button>
          <button class="btn btn-secondary btn-md" id="btn-mono-pass" ${!isMine ? 'disabled' : ''}>
            ⏩ Bỏ Qua
          </button>
        ` : ''}

        ${phase === 'turn_end' ? `
          <button class="btn btn-primary btn-md" id="btn-mono-end-turn" ${!isMine ? 'disabled' : ''}>
            ✓ Kết Thúc Lượt
          </button>
        ` : ''}
      </div>
    `;
    boardEl.appendChild(centerEl);

    // 2. Render 24 Tiles
    const tiles = this.gameState.tiles || [];
    tiles.forEach((t, idx) => {
      const coord = MONOPOLY_COORDS[idx];
      if (!coord) return;

      const tileEl = document.createElement('div');
      tileEl.className = 'monopoly-tile';
      tileEl.style.gridRow = coord[0];
      tileEl.style.gridColumn = coord[1];
      tileEl.dataset.tileId = t.id;

      // Color bar
      const propState = this.gameState.properties[String(t.id)];
      let ownerMarkerHtml = '';
      let housesBadgeHtml = '';

      if (propState && propState.owner !== null) {
        const owner = this.gameState.players[propState.owner];
        if (owner) {
          ownerMarkerHtml = `<div class="tile-owner-indicator" style="background: ${owner.color};"></div>`;
        }
        if (propState.houses > 0) {
          housesBadgeHtml = `<div class="tile-houses-badge">${'★'.repeat(propState.houses)}</div>`;
        }
      }

      // Players on this tile
      const playersOnTile = this.gameState.players.filter(p => !p.is_bankrupt && p.position === t.id);
      const playersHtml = playersOnTile.map(p => `
        <span class="player-token-icon" title="${p.name}">${p.symbol}</span>
      `).join('');

      tileEl.innerHTML = `
        <div class="tile-color-bar" style="background: ${t.color || 'transparent'};"></div>
        ${ownerMarkerHtml}
        <div class="tile-title">${t.name}</div>
        <div class="tile-players-box">${playersHtml}</div>
        ${t.price ? `<div class="tile-price">$${t.price}</div>` : ''}
        ${housesBadgeHtml}
      `;

      boardEl.appendChild(tileEl);
    });
  }

  static updateHUD() {
    const textEl = document.getElementById('mono-turn-text');
    const dotEl = document.getElementById('mono-turn-dot');
    const playersListEl = document.getElementById('mono-players-list');
    const buildableListEl = document.getElementById('mono-buildable-list');

    if (!this.gameState) return;

    const currIdx = this.gameState.current_player;
    const player = this.gameState.players[currIdx];
    const isMine = this.isMyTurn();
    const scores = AppState.currentRoom?.session_scores || {};

    if (textEl && dotEl && player) {
      dotEl.style.background = player.color;
      if (this.gameState.status === 'finished') {
        const winner = this.gameState.winner;
        textEl.innerHTML = `🏆 <strong>${winner.name}</strong> là người sống sót duy nhất và trở thành ĐẠI TỶ PHÚ!`;
        if (!this.gameOverModalShown) {
          this.gameOverModalShown = true;
          this.showGameOverModal(winner);
        }
      } else {
        this.gameOverModalShown = false;
        if (isMine) {
          textEl.innerHTML = `✨ <strong>Lượt của BẠN (${player.symbol})!</strong>`;
        } else {
          textEl.innerHTML = `⏳ Đang đợi <strong>${player.name} (${player.symbol})</strong> thao tác...`;
        }
      }
    }

    if (playersListEl) {
      playersListEl.innerHTML = this.gameState.players.map(p => {
        const isCurrent = p.player_index === currIdx;
        return `
          <div class="player-cash-card ${isCurrent ? 'active-turn' : ''}">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-size: 1.25rem;">${p.symbol}</span>
              <div>
                <strong style="color: ${p.color};">${p.name}</strong>
                <div style="font-size: 0.72rem; color: var(--color-dusty-rose);">
                  ${p.is_bankrupt ? '💥 ĐÃ PHÁ SẢN' : (p.in_jail ? '🚨 Đang trong tù' : `Sở hữu ${p.properties.length} đất`)}
                </div>
              </div>
            </div>
            <div style="text-align: right;">
              <div class="cash-amount" style="${p.is_bankrupt ? 'color: var(--color-danger);' : ''}">
                ${p.is_bankrupt ? '$0' : `$${p.cash}`}
              </div>
              <span class="session-score-pill">Thắng: ${scores[String(p.player_index)] || 0}</span>
            </div>
          </div>
        `;
      }).join('');
    }

    // Buildable list
    if (buildableListEl) {
      const myPlayer = this.gameState.players.find(p => p.player_index === AppState.playerIndex) || player;
      const myProps = myPlayer.properties || [];
      const tiles = this.gameState.tiles || [];

      if (myProps.length === 0) {
        buildableListEl.innerHTML = `<span style="font-size: 0.8rem; color: var(--color-dusty-rose);">Bạn chưa sở hữu mảnh đất nào.</span>`;
      } else {
        buildableListEl.innerHTML = myProps.map(tId => {
          const t = tiles.find(tile => tile.id === tId);
          if (!t || t.type !== 'property') return '';
          const propState = this.gameState.properties[String(tId)];
          const houses = propState?.houses || 0;
          const cost = t.house_cost || 50;
          const canBuild = isMine && houses < 3 && myPlayer.cash >= cost;

          return `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.3rem 0.5rem; background: rgba(37,22,32,0.6); border-radius: var(--radius-sm);">
              <div>
                <strong style="font-size: 0.8rem; color: var(--color-cream);">${t.name}</strong>
                <div style="font-size: 0.7rem; color: #ffbe0b;">${houses < 3 ? `${houses}/3 nhà ($${cost}/nhà)` : 'Đã tối đa 3 nhà'}</div>
              </div>
              ${houses < 3 ? `
                <button class="btn btn-secondary btn-sm btn-build-house" data-tile-id="${t.id}" ${!canBuild ? 'disabled' : ''}>
                  🔨 +1 Nhà
                </button>
              ` : ''}
            </div>
          `;
        }).join('');
      }
    }
  }

  static async sendAction(action) {
    if (!this.isMyTurn()) {
      Toast.error('Chưa đến lượt của bạn');
      return;
    }

    if (!this.isLocal && ApiService.socket && ApiService.socket.connected) {
      ApiService.sendActionSocket(this.roomCode, AppState.participantToken, action, this.stateVersion);
    } else {
      try {
        const res = await ApiService.sendActionRest(this.roomCode, AppState.participantToken, action, this.stateVersion);
        if (res.success) {
          this.gameState = res.room.game_state;
          this.stateVersion = res.room.state_version;
          this.renderGame();
        } else {
          Toast.error(res.error || 'Nước đi không hợp lệ');
        }
      } catch (err) {
        Toast.error('Lỗi khi gửi hành động');
      }
    }
  }

  static async triggerRestart() {
    if (this.isLocal) {
      try {
        const res = await ApiService.restartGameRest(this.roomCode, AppState.participantToken);
        if (res.success) {
          Toast.success('Đã bắt đầu ván mới!');
          this.gameState = res.room.game_state;
          this.stateVersion = res.room.state_version;
          this.renderGame();
        }
      } catch (e) {
        Toast.error('Không thể chơi lại');
      }
    } else {
      if (ApiService.socket && ApiService.socket.connected) {
        ApiService.requestRematchSocket(this.roomCode, AppState.participantToken);
      } else {
        await ApiService.requestRematchRest(this.roomCode, AppState.participantToken);
      }
      Toast.info('Đã gửi yêu cầu tái đấu. Chờ đối thủ đồng ý...');
      const btn = document.getElementById('btn-mono-restart');
      if (btn) {
        btn.textContent = '⏳ Chờ Đối Thủ...';
        btn.disabled = true;
      }
    }
  }

  static showGameOverModal(winner) {
    const scores = AppState.currentRoom?.session_scores || {};
    const scoreText = `Tỉ số phiên: ${scores['0'] || 0} - ${scores['1'] || 0}`;

    const contentHtml = `
      <div class="victory-modal-content">
        <div class="victory-icon">🎩</div>
        <div class="victory-title">Đại Tỷ Phú Bất Động Sản!</div>
        <div class="victory-detail">
          Chúc mừng tỷ phú <strong>${winner?.name || 'Người chơi'}</strong> đã thâu tóm toàn bộ thị trường và trở thành người sống sót giàu có nhất!
          <br>
          <span style="font-weight: 800; color: var(--color-cream); font-size: 1.15rem; display: inline-block; margin-top: 0.5rem;">
            ${scoreText}
          </span>
        </div>
        <div class="victory-actions">
          <button class="btn btn-primary" id="modal-btn-rematch">
            <span>🔄</span> ${this.isLocal ? 'Chơi Lại Ván Mới' : 'Yêu Cầu Tái Đấu'}
          </button>
          <button class="btn btn-sunset" id="modal-btn-room">
            <span>🏠</span> Về Phòng
          </button>
          <button class="btn btn-secondary" id="modal-btn-leave">
            <span>🚪</span> Về Trang Chủ
          </button>
        </div>
      </div>
    `;

    Modal.open('Kết Quả Trận Đấu', contentHtml);

    document.getElementById('modal-btn-rematch')?.addEventListener('click', () => {
      Modal.close();
      this.triggerRestart();
    });

    document.getElementById('modal-btn-room')?.addEventListener('click', () => {
      Modal.close();
      this.returnToRoom();
    });

    document.getElementById('modal-btn-leave')?.addEventListener('click', () => {
      Modal.close();
      this.leaveMatch();
    });
  }

  static async returnToRoom() {
    if (this.isLocal) {
      Router.navigate('local_setup', { game: 'monopoly' });
    } else {
      try {
        if (ApiService.socket && ApiService.socket.connected) {
          ApiService.returnToLobbySocket(this.roomCode, AppState.participantToken);
        } else {
          const res = await ApiService.returnToLobbyRest(this.roomCode, AppState.participantToken);
          if (res.success) {
            AppState.setRoom(res.room);
            Router.navigate('online_lobby', { roomCode: this.roomCode, mode: 'lobby' });
          } else {
            Toast.error(res.error || 'Không thể về phòng');
          }
        }
      } catch (e) {
        console.error(e);
        Toast.error('Lỗi khi trở về phòng');
      }
    }
  }

  static leaveMatch() {
    LeaveRoomHelper.promptLeave(this.roomCode, AppState.participantToken, AppState.isHost, this.isLocal);
  }

  static cleanup() {
    if (this.currentCleanup) {
      this.currentCleanup();
      this.currentCleanup = null;
    }
  }

  static attachEvents() {
    this.cleanup();

    // Center board controls delegation
    const boardEl = document.getElementById('monopoly-board');
    const handleCenterClick = (e) => {
      if (e.target.id === 'btn-mono-roll') {
        this.sendAction({ type: 'roll_dice' });
      } else if (e.target.id === 'btn-mono-buy') {
        this.sendAction({ type: 'buy_property' });
      } else if (e.target.id === 'btn-mono-pass') {
        this.sendAction({ type: 'pass_buy' });
      } else if (e.target.id === 'btn-mono-pay-jail') {
        this.sendAction({ type: 'pay_jail_fine' });
      } else if (e.target.id === 'btn-mono-end-turn') {
        this.sendAction({ type: 'end_turn' });
      }
    };
    boardEl?.addEventListener('click', handleCenterClick);

    // Build house delegation
    const buildableListEl = document.getElementById('mono-buildable-list');
    const handleBuildClick = (e) => {
      const btn = e.target.closest('.btn-build-house');
      if (!btn) return;
      const tileId = parseInt(btn.dataset.tileId, 10);
      this.sendAction({ type: 'build_house', tile_id: tileId });
    };
    buildableListEl?.addEventListener('click', handleBuildClick);

    // Header buttons
    document.getElementById('btn-mono-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: 'monopoly' });
    });

    document.getElementById('btn-mono-switch')?.addEventListener('click', () => {
      SwitchGameModal.open(this.roomCode, AppState.participantToken);
    });

    document.getElementById('btn-mono-room')?.addEventListener('click', () => {
      this.returnToRoom();
    });

    document.getElementById('btn-mono-restart')?.addEventListener('click', () => {
      this.triggerRestart();
    });

    document.getElementById('btn-mono-leave')?.addEventListener('click', () => {
      this.leaveMatch();
    });

    // Socket listeners
    const onGameUpdate = (data) => {
      if (data.room_code === this.roomCode) {
        this.gameState = data.game_state;
        this.stateVersion = data.state_version;
        this.renderGame();
      }
    };

    const onGameRestarted = (data) => {
      if (data.room_code === this.roomCode) {
        Toast.success('Cả hai đã đồng ý! Ván đấu bắt đầu lại!');
        if (data.session_scores && AppState.currentRoom) {
          AppState.currentRoom.session_scores = data.session_scores;
        }
        const btn = document.getElementById('btn-mono-restart');
        if (btn) {
          btn.textContent = '🔄 Đấu Lại';
          btn.disabled = false;
        }
        this.gameState = data.game_state;
        this.stateVersion = data.state_version;
        this.renderGame();
      }
    };

    const onRematchRequested = (data) => {
      if (data.room_code === this.roomCode) {
        if (data.player_index !== AppState.playerIndex) {
          RematchModal.showInvitation(this.roomCode, AppState.participantToken, data.requested_by);
        }
      }
    };

    const onRematchDeclined = (data) => {
      if (data.room_code === this.roomCode) {
        Toast.info(data.message || 'Đối thủ đã từ chối yêu cầu chơi lại.');
        const btn = document.getElementById('btn-mono-restart');
        if (btn) {
          btn.textContent = '🔄 Đấu Lại';
          btn.disabled = false;
        }
      }
    };

    const onRoomGameChanged = (data) => {
      Modal.close();
      Toast.info(`Chủ phòng đã đổi trò chơi sang: ${data.new_game_type}`);
      AppState.setRoom(data.room);
      Router.navigate('online_lobby', { roomCode: data.room.room_code, mode: 'lobby' });
    };

    const onRoomReturnedToLobby = (data) => {
      Modal.close();
      Toast.info(`${data.requested_by || 'Chủ phòng'} đã đưa cả phòng về sảnh.`);
      AppState.setRoom(data.room);
      Router.navigate('online_lobby', { roomCode: data.room?.room_code || this.roomCode, mode: 'lobby' });
    };

    ApiService.on('game_update', onGameUpdate);
    ApiService.on('game_restarted', onGameRestarted);
    ApiService.on('rematch_requested', onRematchRequested);
    ApiService.on('rematch_declined', onRematchDeclined);
    ApiService.on('room_game_changed', onRoomGameChanged);
    ApiService.on('room_returned_to_lobby', onRoomReturnedToLobby);

    this.currentCleanup = () => {
      boardEl?.removeEventListener('click', handleCenterClick);
      buildableListEl?.removeEventListener('click', handleBuildClick);
      ApiService.off('game_update', onGameUpdate);
      ApiService.off('game_restarted', onGameRestarted);
      ApiService.off('rematch_requested', onRematchRequested);
      ApiService.off('rematch_declined', onRematchDeclined);
      ApiService.off('room_game_changed', onRoomGameChanged);
      ApiService.off('room_returned_to_lobby', onRoomReturnedToLobby);
    };
  }
}
