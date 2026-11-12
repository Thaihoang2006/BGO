import { AppState } from '../../state.js';
import { Router } from '../../router.js';
import { Toast } from '../../components/toast.js';
import { Modal } from '../../components/modal.js';
import { ApiService } from '../../api.js';
import { SwitchGameModal } from '../../components/switchGameModal.js';
import { RematchModal } from '../../components/rematchModal.js';
import { LeaveRoomHelper } from '../../components/leaveRoomHelper.js';

export class CaroGameView {
  static currentCleanup = null;
  static boardState = null;
  static stateVersion = 0;
  static isLocal = false;
  static roomCode = null;
  static gameOverModalShown = false;

  static async render(container, params = {}) {
    const roomCode = params.roomCode || AppState.roomCode;
    if (!roomCode) {
      Router.navigate('home');
      return;
    }

    this.roomCode = roomCode;
    this.gameOverModalShown = false;

    // Fetch latest room data
    try {
      const res = await ApiService.getRoom(roomCode, AppState.participantToken);
      if (!res.room) {
        Toast.error('Không tìm thấy phòng chơi');
        Router.navigate('home');
        return;
      }
      AppState.setRoom(res.room);
      this.isLocal = res.room.is_local;
      this.boardState = res.room.game_state;
      this.stateVersion = res.room.state_version;
    } catch (e) {
      console.error(e);
      Toast.error('Không thể tải bàn chơi');
      return;
    }

    // Connect socket if not connected
    if (!this.isLocal) {
      ApiService.joinRoomSocket(roomCode, AppState.participantToken);
    }

    const rows = this.boardState?.rows || 15;
    const cols = this.boardState?.cols || 15;

    container.innerHTML = `
      <div class="game-play-container">
        <!-- Match Header -->
        <div class="glass-panel match-header">
          <div class="match-room-info">
            <span class="match-game-title" id="caro-title-size">Cờ Caro (${rows}x${cols})</span>
            <span class="match-mode-badge">${this.isLocal ? '💻 Local (1 Máy)' : `🌐 Phòng: ${roomCode}`}</span>
          </div>

          <div class="match-controls">
            <button class="btn btn-secondary btn-sm" id="btn-in-game-rules">
              📖 Luật Chơi
            </button>
            <button class="btn btn-secondary btn-sm" id="btn-in-game-switch">
              🎮 Đổi Trò
            </button>
            <button class="btn btn-sunset btn-sm" id="btn-in-game-room">
              🏠 Về Phòng
            </button>
            <button class="btn btn-ghost btn-sm" id="btn-in-game-leave">
              🚪 Rời Bàn
            </button>
          </div>
        </div>

        <!-- Turn Announcement Banner -->
        <div class="turn-banner" id="caro-turn-banner">
          <div class="turn-indicator-dot" id="turn-dot"></div>
          <div class="turn-text" id="turn-text">Đang tải bàn cờ...</div>
        </div>

        <!-- Players HUD Area -->
        <div class="players-hud" id="caro-players-hud">
          <!-- Rendered dynamically -->
        </div>

        <!-- Caro Expanding Board -->
        <div class="board-wrapper" id="caro-board-wrapper">
          <div class="caro-board" id="caro-grid-board">
            <!-- cells generated dynamically -->
          </div>
        </div>
      </div>
    `;

    this.renderBoard();
    this.updateHUD();
    this.attachEvents();
  }

  static renderBoard() {
    const boardEl = document.getElementById('caro-grid-board');
    if (!boardEl || !this.boardState) return;

    const grid = this.boardState.grid || [];
    const rows = this.boardState.rows || this.boardState.board_size || 15;
    const cols = this.boardState.cols || this.boardState.board_size || 15;
    const lastMove = this.boardState.last_move;
    const winner = this.boardState.winner;
    const winningPoints = new Set();

    const titleEl = document.getElementById('caro-title-size');
    if (titleEl) {
      titleEl.textContent = `Cờ Caro (${rows}x${cols})`;
    }

    if (winner && winner.winning_line) {
      winner.winning_line.forEach(([r, c]) => winningPoints.add(`${r},${c}`));
    }

    const starPoints = new Set(['3,3', '3,11', '7,7', '11,3', '11,11']);
    const isGameOver = this.boardState.status === 'finished';
    const isMyTurn = this.checkIsMyTurn();

    boardEl.style.gridTemplateColumns = `repeat(${cols}, 38px)`;
    boardEl.style.gridTemplateRows = `repeat(${rows}, 38px)`;
    boardEl.innerHTML = '';

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = document.createElement('div');
        cell.className = 'caro-cell';
        cell.dataset.row = r;
        cell.dataset.col = c;

        if (starPoints.has(`${r},${c}`)) {
          cell.classList.add('star-point');
        }

        const stone = grid[r] ? grid[r][c] : null;

        if (stone) {
          const piece = document.createElement('div');
          piece.className = `caro-piece ${stone === 'X' ? 'piece-x' : 'piece-o'}`;
          piece.textContent = stone;

          if (lastMove && lastMove.row === r && lastMove.col === c) {
            piece.classList.add('last-move-marker');
          }

          if (winningPoints.has(`${r},${c}`)) {
            piece.classList.add('winning-piece');
          }

          cell.appendChild(piece);
        } else if (!isGameOver && isMyTurn) {
          cell.classList.add('hover-preview');
        }

        boardEl.appendChild(cell);
      }
    }
  }

  static updateHUD() {
    if (!this.boardState) return;

    const hudEl = document.getElementById('caro-players-hud');
    const turnText = document.getElementById('turn-text');
    const turnDot = document.getElementById('turn-dot');
    const banner = document.getElementById('caro-turn-banner');

    const players = this.boardState.players || [];
    const currIdx = this.boardState.current_player;
    const isGameOver = this.boardState.status === 'finished';
    const winner = this.boardState.winner;
    const scores = AppState.currentRoom?.session_scores || {};

    // HUD Cards
    if (hudEl) {
      const cardsHtml = players.map(p => {
        const isCurrent = !isGameOver && p.player_index === currIdx;
        const movesCount = (this.boardState.history || []).filter(h => h.player_index === p.player_index).length;
        const pScore = scores[String(p.player_index)] || 0;

        return `
          <div class="player-hud-card ${isCurrent ? 'is-turn' : ''}">
            <div class="hud-stone-symbol" style="background: ${p.color}; color: #251620;">
              ${p.symbol}
            </div>
            <div class="hud-player-details">
              <h4>
                ${p.name}
                ${p.player_index === 0 ? '<span style="font-size:0.75rem; color:var(--color-sunset-orange);">(Đi trước)</span>' : ''}
              </h4>
              <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.2rem;">
                <span class="session-score-pill">Thắng: ${pScore}</span>
                <span>${movesCount} nước</span>
              </div>
            </div>
          </div>
        `;
      });

      const centerDividerHtml = `
        <div class="session-score-center">
          <div class="score-display-box">${scores['0'] || 0} - ${scores['1'] || 0}</div>
          <span style="font-size: 0.75rem; color: var(--color-dusty-rose); font-weight: 700; text-transform: uppercase;">Tỉ số ván</span>
        </div>
      `;

      hudEl.innerHTML = cardsHtml[0] + centerDividerHtml + (cardsHtml[1] || '');
    }

    // Turn Banner
    if (isGameOver) {
      if (winner && winner.win_reason === 'draw') {
        turnText.textContent = '🤝 Trận đấu hòa!';
        turnDot.style.background = 'var(--color-warning)';
      } else if (winner) {
        turnText.innerHTML = `🏆 <strong>${winner.name} (${winner.symbol})</strong> đã chiến thắng! Tỉ số hiện tại: <strong>${scores['0'] || 0} - ${scores['1'] || 0}</strong>`;
        turnDot.style.background = 'var(--color-success)';
      }
      banner?.classList.remove('active-turn-glow');
    } else {
      const activePlayer = players.find(p => p.player_index === currIdx) || {};
      const isMyTurn = this.checkIsMyTurn();

      if (this.isLocal) {
        turnText.innerHTML = `Lượt đi của: <strong style="color: ${activePlayer.color};">${activePlayer.name} (${activePlayer.symbol})</strong>`;
      } else {
        if (isMyTurn) {
          turnText.innerHTML = `✨ <strong>Lượt của BẠN (${activePlayer.symbol})!</strong> Hãy đặt quân cờ`;
        } else {
          turnText.innerHTML = `⏳ Đang đợi <strong>${activePlayer.name} (${activePlayer.symbol})</strong> đi nước...`;
        }
      }

      turnDot.style.background = activePlayer.color || 'var(--color-sunset-orange)';
      banner?.classList.add('active-turn-glow');
    }
  }

  static checkIsMyTurn() {
    if (!this.boardState || this.boardState.status !== 'playing') return false;
    if (this.isLocal) return true;
    return AppState.playerIndex === this.boardState.current_player;
  }

  static async handleCellClick(r, c) {
    if (!this.boardState || this.boardState.status !== 'playing') return;

    if (!this.checkIsMyTurn()) {
      Toast.error('Chưa đến lượt của bạn');
      return;
    }

    if (this.boardState.grid[r] && this.boardState.grid[r][c] !== null) {
      Toast.error('Ô này đã có quân cờ');
      return;
    }

    const action = {
      type: 'place_piece',
      row: r,
      col: c
    };

    // Client-side optimistic preview
    const activePlayer = this.boardState.players.find(p => p.player_index === this.boardState.current_player);
    const cellEl = document.querySelector(`.caro-cell[data-row="${r}"][data-col="${c}"]`);
    if (cellEl && activePlayer) {
      const piece = document.createElement('div');
      piece.className = `caro-piece ${activePlayer.symbol === 'X' ? 'piece-x' : 'piece-o'}`;
      piece.textContent = activePlayer.symbol;
      cellEl.innerHTML = '';
      cellEl.appendChild(piece);
    }

    // Submit action
    if (!this.isLocal && ApiService.socket && ApiService.socket.connected) {
      ApiService.sendActionSocket(this.roomCode, AppState.participantToken, action, this.stateVersion);
    } else {
      try {
        const res = await ApiService.sendActionRest(this.roomCode, AppState.participantToken, action, this.stateVersion);
        if (res.success) {
          if (res.event?.board_expanded) {
            Toast.info(`Bàn cờ đã mở rộng (${res.event.rows}x${res.event.cols})!`);
          }
          if (res.room) {
            AppState.setRoom(res.room);
          }
          this.applyUpdate(res.room.game_state, res.room.state_version, res.room.winner, res.room.session_scores);
        } else {
          Toast.error(res.error || 'Nước đi không hợp lệ');
          this.renderBoard();
        }
      } catch (e) {
        console.error(e);
        Toast.error('Lỗi khi gửi nước đi');
        this.renderBoard();
      }
    }
  }

  static applyUpdate(newGameState, newVersion, winnerInfo = null, sessionScores = null) {
    this.boardState = newGameState;
    this.stateVersion = newVersion;
    if (sessionScores && AppState.currentRoom) {
      AppState.currentRoom.session_scores = sessionScores;
    }
    if (newGameState && newGameState.session_scores && AppState.currentRoom) {
      AppState.currentRoom.session_scores = newGameState.session_scores;
    }
    this.renderBoard();
    this.updateHUD();

    if (this.boardState.status === 'finished') {
      if (!this.gameOverModalShown) {
        this.gameOverModalShown = true;
        this.showGameOverModal(winnerInfo || this.boardState.winner);
      }
    } else {
      this.gameOverModalShown = false;
    }
  }

  static showGameOverModal(winner) {
    let contentHtml = '';
    const scores = AppState.currentRoom?.session_scores || this.boardState?.session_scores || {};
    const scoreText = `Tỉ số trận đấu: ${scores['0'] || 0} - ${scores['1'] || 0}`;

    if (!winner || winner.win_reason === 'draw') {
      contentHtml = `
        <div class="victory-modal-content">
          <div class="victory-icon">🤝</div>
          <div class="victory-title">Hòa Cờ!</div>
          <div class="victory-detail">
            Hai kỳ thủ ngang tài ngang sức.<br>
            <span style="font-weight: 800; color: var(--color-cream); font-size: 1.15rem; display: inline-block; margin-top: 0.5rem;">
              ${scoreText}
            </span>
          </div>
          <div class="victory-actions">
            <button class="btn btn-primary" id="modal-btn-rematch">
              <span>🔄</span> ${this.isLocal ? 'Chơi Lại' : 'Yêu Cầu Tái Đấu'}
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
    } else {
      contentHtml = `
        <div class="victory-modal-content">
          <div class="victory-icon">🏆</div>
          <div class="victory-title">Chiến Thắng Tuyệt Đối!</div>
          <div class="victory-detail">
            Chúc mừng <strong>${winner.name} (Quân ${winner.symbol})</strong> đã tạo nên chuỗi 5 quân liên tiếp!
            <br>
            <span style="font-weight: 800; color: var(--color-cream); font-size: 1.15rem; display: inline-block; margin-top: 0.5rem;">
              ${scoreText}
            </span>
          </div>
          <div class="victory-actions">
            <button class="btn btn-primary" id="modal-btn-rematch">
              <span>🔄</span> ${this.isLocal ? 'Chơi Lại' : 'Yêu Cầu Tái Đấu'}
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
    }

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
      Router.navigate('local_setup', { game: 'caro' });
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

  static async triggerRestart() {
    if (this.isLocal) {
      try {
        const res = await ApiService.restartGameRest(this.roomCode, AppState.participantToken);
        if (res.success) {
          Toast.success('Đã bắt đầu ván mới!');
          if (res.room) {
            AppState.setRoom(res.room);
          }
          this.gameOverModalShown = false;
          this.applyUpdate(res.room.game_state, res.room.state_version, null, res.room.session_scores);
        } else {
          Toast.error(res.error || 'Không thể bắt đầu lại');
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
      const btn = document.getElementById('btn-in-game-restart');
      if (btn) {
        btn.textContent = '⏳ Chờ Đối Thủ...';
        btn.disabled = true;
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

    const boardEl = document.getElementById('caro-grid-board');
    const boardClickHandler = (e) => {
      const cell = e.target.closest('.caro-cell');
      if (!cell) return;
      const r = parseInt(cell.dataset.row, 10);
      const c = parseInt(cell.dataset.col, 10);
      this.handleCellClick(r, c);
    };
    boardEl?.addEventListener('click', boardClickHandler);

    // Header buttons
    document.getElementById('btn-in-game-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: 'caro' });
    });

    document.getElementById('btn-in-game-switch')?.addEventListener('click', () => {
      SwitchGameModal.open(this.roomCode, AppState.participantToken);
    });

    document.getElementById('btn-in-game-room')?.addEventListener('click', () => {
      this.returnToRoom();
    });

    document.getElementById('btn-in-game-restart')?.addEventListener('click', () => {
      this.triggerRestart();
    });

    document.getElementById('btn-in-game-leave')?.addEventListener('click', () => {
      this.leaveMatch();
    });

    // Socket real-time events
    const onGameUpdate = (data) => {
      if (data.room_code === this.roomCode) {
        if (data.event?.board_expanded) {
          Toast.info(`Bàn cờ đã mở rộng (${data.event.rows}x${data.event.cols})!`);
        }
        if (data.room) {
          AppState.setRoom(data.room);
        } else if (data.session_scores && AppState.currentRoom) {
          AppState.currentRoom.session_scores = data.session_scores;
        }
        this.applyUpdate(data.game_state, data.state_version, data.winner, data.session_scores || data.room?.session_scores);
      }
    };

    const onGameRestarted = (data) => {
      if (data.room_code === this.roomCode) {
        Toast.success('Cả hai đã đồng ý! Ván đấu bắt đầu lại!');
        if (data.room) {
          AppState.setRoom(data.room);
        } else if (data.session_scores && AppState.currentRoom) {
          AppState.currentRoom.session_scores = data.session_scores;
        }
        this.gameOverModalShown = false;
        const btn = document.getElementById('btn-in-game-restart');
        if (btn) {
          btn.textContent = '🔄 Đấu Lại';
          btn.disabled = false;
        }
        this.applyUpdate(data.game_state, data.state_version, null, data.session_scores || data.room?.session_scores);
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
        const btn = document.getElementById('btn-in-game-restart');
        if (btn) {
          btn.textContent = '🔄 Đấu Lại';
          btn.disabled = false;
        }
      }
    };

    const onRoomGameChanged = (data) => {
      Modal.close();
      Toast.info(`Chủ phòng đã đổi sang trò: ${data.new_game_type}`);
      AppState.setRoom(data.room);
      Router.navigate('online_lobby', { roomCode: data.room.room_code, mode: 'lobby' });
    };

    const onRoomReturnedToLobby = (data) => {
      Modal.close();
      Toast.info(`${data.requested_by || 'Chủ phòng'} đã đưa cả phòng về sảnh.`);
      AppState.setRoom(data.room);
      Router.navigate('online_lobby', { roomCode: data.room.room_code, mode: 'lobby' });
    };

    const onPlayerDisconnected = (data) => {
      Toast.error(`${data.name} bị mất kết nối!`);
    };

    const onPlayerConnected = (data) => {
      Toast.info(`${data.name} đã kết nối lại.`);
    };

    ApiService.on('game_update', onGameUpdate);
    ApiService.on('game_restarted', onGameRestarted);
    ApiService.on('rematch_requested', onRematchRequested);
    ApiService.on('rematch_declined', onRematchDeclined);
    ApiService.on('room_game_changed', onRoomGameChanged);
    ApiService.on('room_returned_to_lobby', onRoomReturnedToLobby);
    ApiService.on('player_disconnected', onPlayerDisconnected);
    ApiService.on('player_connected', onPlayerConnected);

    this.currentCleanup = () => {
      boardEl?.removeEventListener('click', boardClickHandler);
      ApiService.off('game_update', onGameUpdate);
      ApiService.off('game_restarted', onGameRestarted);
      ApiService.off('rematch_requested', onRematchRequested);
      ApiService.off('rematch_declined', onRematchDeclined);
      ApiService.off('room_game_changed', onRoomGameChanged);
      ApiService.off('room_returned_to_lobby', onRoomReturnedToLobby);
      ApiService.off('player_disconnected', onPlayerDisconnected);
      ApiService.off('player_connected', onPlayerConnected);
    };
  }
}
