import { AppState } from '../../state.js';
import { Router } from '../../router.js';
import { Toast } from '../../components/toast.js';
import { Modal } from '../../components/modal.js';
import { ApiService } from '../../api.js';
import { SwitchGameModal } from '../../components/switchGameModal.js';
import { RematchModal } from '../../components/rematchModal.js';
import { LeaveRoomHelper } from '../../components/leaveRoomHelper.js';

// Pre-computed grid coordinates (row, col from 0..14) for the 56 perimeter track steps
// Exactly matches classic Vietnamese Ludo board layout:
// Quadrant 0: Red (Bottom-Left)   - start step 0  at [8, 0],  exit arrow ➡
// Quadrant 1: Green (Bottom-Right) - start step 14 at [14, 8], exit arrow ⬆
// Quadrant 2: Yellow (Top-Right)   - start step 28 at [6, 14], exit arrow ⬅
// Quadrant 3: Cyan (Top-Left)      - start step 42 at [0, 6],  exit arrow ⬇
const TRACK_COORDS = [
  // Quadrant 0 (Red / Bottom-Left) - 14 steps (0..13)
  [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5],
  [8, 6],
  [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6],
  [14, 7],

  // Quadrant 1 (Green / Bottom-Right) - 14 steps (14..27)
  [14, 8], [13, 8], [12, 8], [11, 8], [10, 8], [9, 8],
  [8, 8],
  [8, 9], [8, 10], [8, 11], [8, 12], [8, 13], [8, 14],
  [7, 14],

  // Quadrant 2 (Yellow / Top-Right) - 14 steps (28..41)
  [6, 14], [6, 13], [6, 12], [6, 11], [6, 10], [6, 9],
  [6, 8],
  [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
  [0, 7],

  // Quadrant 3 (Cyan / Top-Left) - 14 steps (42..55)
  [0, 6], [1, 6], [2, 6], [3, 6], [4, 6], [5, 6],
  [6, 6],
  [6, 5], [6, 4], [6, 3], [6, 2], [6, 1], [6, 0],
  [7, 0]
];

// Home column tiers (1..6) for players 0..3 leading to center [7, 7]
const HOME_COORDS = {
  // Player 0 (Red, Bottom-Left): entered from step 55 [7, 0], moves right along row 7
  0: [[7, 1], [7, 2], [7, 3], [7, 4], [7, 5], [7, 6]],
  // Player 1 (Green, Bottom-Right): entered from step 13 [14, 7], moves up along col 7
  1: [[13, 7], [12, 7], [11, 7], [10, 7], [9, 7], [8, 7]],
  // Player 2 (Yellow, Top-Right): entered from step 27 [7, 14], moves left along row 7
  2: [[7, 13], [7, 12], [7, 11], [7, 10], [7, 9], [7, 8]],
  // Player 3 (Cyan, Top-Left): entered from step 41 [0, 7], moves down along col 7
  3: [[1, 7], [2, 7], [3, 7], [4, 7], [5, 7], [6, 7]]
};

const DICE_FACES = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];

export class LudoGameView {
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
      <div class="ludo-container">
        <!-- Header -->
        <div class="glass-panel match-header">
          <div class="match-room-info">
            <span class="match-game-title">Cờ Cá Ngựa (Ludo)</span>
            <span class="match-mode-badge">${this.isLocal ? '💻 Local (1 Máy)' : `🌐 Phòng: ${roomCode}`}</span>
          </div>

          <div class="match-controls">
            <button class="btn btn-secondary btn-sm" id="btn-ludo-rules">📖 Luật Chơi</button>
            <button class="btn btn-secondary btn-sm" id="btn-ludo-switch">🎮 Đổi Trò</button>
            <button class="btn btn-sunset btn-sm" id="btn-ludo-room">🏠 Về Phòng</button>
            <button class="btn btn-ghost btn-sm" id="btn-ludo-leave">🚪 Rời Bàn</button>
          </div>
        </div>

        <!-- Turn Banner -->
        <div class="turn-banner" id="ludo-turn-banner">
          <div class="turn-indicator-dot" id="ludo-turn-dot"></div>
          <div class="turn-text" id="ludo-turn-text">Đang tải bàn cờ...</div>
        </div>

        <!-- Match Layout: Board + Controls -->
        <div class="ludo-layout">
          <div class="ludo-board-wrapper">
            <div class="ludo-board" id="ludo-board">
              <!-- Grid generated dynamically -->
            </div>
          </div>

          <!-- Controls sidebar -->
          <div class="ludo-control-panel">
            <!-- Waiting banner when it's NOT my turn -->
            <div class="glass-panel" id="ludo-waiting-turn-box" style="display: none; padding: 1.25rem; text-align: center; border-radius: var(--radius-md); margin-bottom: 1.25rem; border: 1px solid var(--surface-glass-border);">
              <div style="font-size: 2.2rem; margin-bottom: 0.5rem; animation: pulse 2s infinite;">⏳</div>
              <h4 style="color: var(--color-cream); font-size: 1rem; margin-bottom: 0.35rem;" id="ludo-waiting-title">Đang đợi đối thủ...</h4>
              <p style="color: var(--color-dusty-rose); font-size: 0.82rem; margin: 0;">Chưa đến lượt của bạn. Xúc xắc được cất tạm cho đến khi tới lượt bạn.</p>
            </div>

            <!-- Dice roller box (visible only when it IS my turn or Local) -->
            <div class="glass-panel dice-roller-box" id="ludo-dice-box">
              <div class="dice-display" id="ludo-dice-face">🎲</div>
              <button class="btn btn-primary btn-lg" id="btn-roll-dice" style="width: 100%;">
                🎲 Gieo Xúc Xắc
              </button>
              <p id="ludo-action-tip" style="margin-top: 0.8rem; font-size: 0.85rem; color: var(--color-dusty-rose);">
                Đến lượt của bạn, hãy nhấn Gieo Xúc Xắc!
              </p>
            </div>

            <!-- Player & Horses status -->
            <div class="glass-panel ludo-horses-status-card" id="ludo-horses-status">
              <!-- Rendered dynamically -->
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
    const boardEl = document.getElementById('ludo-board');
    if (!boardEl || !this.gameState) return;

    boardEl.innerHTML = '';

    const colors = ['#FF4838', '#78C800', '#FFBE0B', '#00BCD4'];
    const quadrantNames = ['Đỏ', 'Xanh Lá', 'Vàng', 'Lam'];

    // 1. Render 4 Stables (Chuồng 4 góc dạng ô vuông theo chuẩn ảnh 2)
    for (let pIdx = 0; pIdx < 4; pIdx++) {
      const stable = document.createElement('div');
      stable.className = `ludo-stable stable-${pIdx}`;
      const player = this.gameState.players[pIdx];
      const pColor = player ? player.color : colors[pIdx];

      stable.innerHTML = `
        <div class="stable-header" style="color: ${pColor};">
          ${player ? player.name : `Chuồng ${quadrantNames[pIdx]}`}
        </div>
        <div class="stable-dock-grid">
          <div class="stable-dock-spot" id="stable-slot-${pIdx}-0"></div>
          <div class="stable-dock-spot" id="stable-slot-${pIdx}-1"></div>
          <div class="stable-dock-spot" id="stable-slot-${pIdx}-2"></div>
          <div class="stable-dock-spot" id="stable-slot-${pIdx}-3"></div>
        </div>
      `;
      boardEl.appendChild(stable);
    }

    // 2. Render Center Destination (Ô đích trung tâm 4 tam giác tụ lại như ảnh 2)
    const centerEl = document.createElement('div');
    centerEl.className = 'ludo-center-destination';
    centerEl.innerHTML = `
      <svg viewBox="0 0 100 100" class="center-triangles-svg">
        <!-- Top triangle: Cyan (Q3) -->
        <polygon points="0,0 100,0 50,50" fill="#00BCD4" />
        <!-- Right triangle: Yellow (Q2) -->
        <polygon points="100,0 100,100 50,50" fill="#FFBE0B" />
        <!-- Bottom triangle: Green (Q1) -->
        <polygon points="100,100 0,100 50,50" fill="#78C800" />
        <!-- Left triangle: Red (Q0) -->
        <polygon points="0,100 0,0 50,50" fill="#FF4838" />
        <!-- Center circle -->
        <circle cx="50" cy="50" r="16" fill="#ffffff" stroke="rgba(0,0,0,0.12)" stroke-width="1" />
      </svg>
      <div class="center-trophy-badge">🏆</div>
    `;
    boardEl.appendChild(centerEl);

    // 3. Render 56 perimeter track cells (Chấm tròn chạy quanh bàn như ảnh 2)
    const startArrows = {
      0: '➡',
      14: '⬆',
      28: '⬅',
      42: '⬇'
    };

    TRACK_COORDS.forEach((coord, stepIdx) => {
      const cell = document.createElement('div');
      cell.className = 'ludo-step';
      cell.style.gridRow = coord[0] + 1;
      cell.style.gridColumn = coord[1] + 1;
      cell.dataset.step = stepIdx;

      // Xác định quadrant màu (0..13: Q0 Đỏ, 14..27: Q1 Xanh, 28..41: Q2 Vàng, 42..55: Q3 Xanh lá)
      const qIdx = Math.floor(stepIdx / 14);
      cell.classList.add(`track-q${qIdx}`);

      // Chấm tròn bên trong mỗi ô
      const spot = document.createElement('div');
      spot.className = `step-spot spot-q${qIdx}`;

      // Nếu là ô xuất phát có mũi tên trắng như ảnh 2
      if (startArrows[stepIdx] !== undefined) {
        cell.classList.add(`start-step-${qIdx}`);
        spot.classList.add('start-spot');
        spot.innerHTML = `<span class="start-arrow">${startArrows[stepIdx]}</span>`;
      }

      cell.appendChild(spot);
      boardEl.appendChild(cell);
    });

    // 4. Render home columns (Các bậc lên chuồng đích 1..6 dạng ô vuông có số)
    Object.entries(HOME_COORDS).forEach(([pIdxStr, coords]) => {
      const pIdx = parseInt(pIdxStr, 10);
      coords.forEach((coord, tierIdx) => {
        const cell = document.createElement('div');
        cell.className = `ludo-home-step home-p${pIdx}`;
        cell.style.gridRow = coord[0] + 1;
        cell.style.gridColumn = coord[1] + 1;
        cell.dataset.homePlayer = pIdx;
        cell.dataset.homeTier = tierIdx + 1;
        cell.innerHTML = `
          <div class="home-tier-badge tier-p${pIdx}">
            <span>${tierIdx + 1}</span>
          </div>
        `;
        boardEl.appendChild(cell);
      });
    });

    // 5. Place horses (Quân cờ tròn nhỏ gọn, không choán bàn)
    const validHorseIds = new Set(this.gameState.valid_horse_ids || []);
    const isMyTurn = this.isMyTurn();
    const currPIdx = this.gameState.current_player;

    this.gameState.players.forEach(p => {
      p.horses.forEach(h => {
        const horseEl = document.createElement('div');
        horseEl.className = `ludo-horse horse-p${p.player_index}`;
        horseEl.innerHTML = `<span class="horse-num">${h.id + 1}</span>`;
        horseEl.title = `${p.name} - Ngựa #${h.id + 1}`;
        horseEl.dataset.horseId = h.id;
        horseEl.dataset.playerIndex = p.player_index;

        const isSelectable = isMyTurn && p.player_index === currPIdx && validHorseIds.has(h.id);
        if (isSelectable) {
          horseEl.classList.add('clickable');
        }

        if (h.status === 'stable') {
          const slot = document.getElementById(`stable-slot-${p.player_index}-${h.id}`);
          slot?.appendChild(horseEl);
        } else if (h.status === 'on_track') {
          const stepCell = boardEl.querySelector(`.ludo-step[data-step="${h.step}"]`);
          stepCell?.appendChild(horseEl);
        } else if (h.status === 'home') {
          const homeCell = boardEl.querySelector(`.ludo-home-step[data-home-player="${p.player_index}"][data-home-tier="${h.step}"]`);
          homeCell?.appendChild(horseEl);
        }
      });
    });
  }

  static updateHUD() {
    const textEl = document.getElementById('ludo-turn-text');
    const dotEl = document.getElementById('ludo-turn-dot');
    const diceFaceEl = document.getElementById('ludo-dice-face');
    const btnRoll = document.getElementById('btn-roll-dice');
    const tipEl = document.getElementById('ludo-action-tip');
    const statusEl = document.getElementById('ludo-horses-status');

    if (!this.gameState) return;

    const currIdx = this.gameState.current_player;
    const player = this.gameState.players[currIdx];
    const isMine = this.isMyTurn();
    const phase = this.gameState.phase;
    const scores = AppState.currentRoom?.session_scores || {};

    if (diceFaceEl) {
      if (this.gameState.dice_value) {
        diceFaceEl.textContent = DICE_FACES[this.gameState.dice_value] || this.gameState.dice_value;
      } else {
        diceFaceEl.textContent = '🎲';
      }
    }

    if (textEl && dotEl && player) {
      dotEl.style.background = player.color;
      if (this.gameState.status === 'finished') {
        const winner = this.gameState.winner;
        textEl.innerHTML = `🏆 <strong>${winner.name}</strong> đã đưa đủ ngựa về chuồng đích và CHIẾN THẮNG!`;
        if (!this.gameOverModalShown) {
          this.gameOverModalShown = true;
          this.showGameOverModal(winner);
        }
      } else {
        this.gameOverModalShown = false;
        if (isMine) {
          if (phase === 'roll') {
            textEl.innerHTML = `✨ <strong>Lượt của BẠN!</strong> Hãy gieo xúc xắc.`;
          } else {
            textEl.innerHTML = `🎯 <strong>Lượt của BẠN!</strong> Hãy nhấp chọn 1 chú ngựa đang nhấp nháy để di chuyển.`;
          }
        } else {
          textEl.innerHTML = `⏳ Đang đợi <strong>${player.name}</strong> thao tác...`;
        }
      }
    }

    // Toggle dice box: if not my turn in Online match, stow away dice
    const diceBoxEl = document.getElementById('ludo-dice-box');
    const waitingBoxEl = document.getElementById('ludo-waiting-turn-box');
    const waitingTitleEl = document.getElementById('ludo-waiting-title');

    if (diceBoxEl && waitingBoxEl) {
      if (!isMine && !this.isLocal && this.gameState.status !== 'finished') {
        diceBoxEl.style.display = 'none';
        waitingBoxEl.style.display = 'block';
        if (waitingTitleEl && player) {
          waitingTitleEl.innerHTML = `Đang đợi <strong>${player.name}</strong>...`;
        }
      } else {
        diceBoxEl.style.display = 'block';
        waitingBoxEl.style.display = 'none';
      }
    }

    if (btnRoll) {
      btnRoll.disabled = !isMine || phase !== 'roll' || this.gameState.status === 'finished';
      btnRoll.textContent = this.gameState.bonus_roll ? '🎲 Gieo Lượt Thưởng (Đổ 6)!' : '🎲 Gieo Xúc Xắc';
    }

    if (tipEl) {
      tipEl.textContent = this.gameState.last_action_desc || '';
    }

    if (statusEl) {
      statusEl.innerHTML = `
        <h4 style="color: var(--color-cream); margin-bottom: 0.75rem; font-size: 0.95rem;">
          🏁 Bảng Điểm & Đội Ngựa
        </h4>
        <div style="display: flex; flex-direction: column; gap: 0.6rem;">
          ${this.gameState.players.map(p => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.4rem 0.6rem; background: rgba(37,22,32,0.6); border-radius: var(--radius-sm); border-left: 3px solid ${p.color};">
              <div>
                <strong style="color: ${p.color};">${p.name}</strong>
                <div style="font-size: 0.75rem; color: var(--color-dusty-rose);">
                  Về đích: ${p.finished_count}/2 ngựa
                </div>
              </div>
              <span class="session-score-pill">Thắng: ${scores[String(p.player_index)] || 0}</span>
            </div>
          `).join('')}
        </div>
      `;
    }
  }

  static async rollDice() {
    if (!this.isMyTurn() || this.gameState.phase !== 'roll') return;

    const diceFaceEl = document.getElementById('ludo-dice-face');
    diceFaceEl?.classList.add('rolling');

    const action = { type: 'roll_dice' };

    if (!this.isLocal && ApiService.socket && ApiService.socket.connected) {
      ApiService.sendActionSocket(this.roomCode, AppState.participantToken, action, this.stateVersion);
    } else {
      try {
        const res = await ApiService.sendActionRest(this.roomCode, AppState.participantToken, action, this.stateVersion);
        if (res.success) {
          diceFaceEl?.classList.remove('rolling');
          this.gameState = res.room.game_state;
          this.stateVersion = res.room.state_version;
          this.renderGame();
        } else {
          diceFaceEl?.classList.remove('rolling');
          Toast.error(res.error || 'Lỗi gieo xúc xắc');
        }
      } catch (err) {
        diceFaceEl?.classList.remove('rolling');
        Toast.error('Lỗi kết nối');
      }
    }
  }

  static async selectHorse(horseId) {
    if (!this.isMyTurn() || this.gameState.phase !== 'select_horse') return;

    const action = { type: 'move_horse', horse_id: horseId };

    if (!this.isLocal && ApiService.socket && ApiService.socket.connected) {
      ApiService.sendActionSocket(this.roomCode, AppState.participantToken, action, this.stateVersion);
    } else {
      try {
        const res = await ApiService.sendActionRest(this.roomCode, AppState.participantToken, action, this.stateVersion);
        if (res.success) {
          this.gameState = res.room.game_state;
          this.stateVersion = res.room.state_version;
          this.renderGame();
          if (res.event?.kicked) {
            Toast.info(`💥 Đã ĐÁ ngựa của ${res.event.kicked.victim_name} về chuồng!`);
          }
        } else {
          Toast.error(res.error || 'Nước đi không hợp lệ');
        }
      } catch (err) {
        Toast.error('Lỗi khi di chuyển ngựa');
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
      const btn = document.getElementById('btn-ludo-restart');
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
        <div class="victory-icon">🐴</div>
        <div class="victory-title">Nhà Vô Địch Đường Đua!</div>
        <div class="victory-detail">
          Chúc mừng kỵ mã <strong>${winner?.name || 'Người chơi'}</strong> đã đưa đủ ngựa về chuồng đích an toàn và giành CHIẾN THẮNG vang dội!
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
      Router.navigate('local_setup', { game: 'ludo' });
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

    // Roll dice button
    document.getElementById('btn-roll-dice')?.addEventListener('click', () => {
      this.rollDice();
    });

    // Board horse click delegation
    const boardEl = document.getElementById('ludo-board');
    const handleHorseClick = (e) => {
      const horseEl = e.target.closest('.ludo-horse.clickable');
      if (!horseEl) return;
      const hId = parseInt(horseEl.dataset.horseId, 10);
      this.selectHorse(hId);
    };
    boardEl?.addEventListener('click', handleHorseClick);

    // Header buttons
    document.getElementById('btn-ludo-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: 'ludo' });
    });

    document.getElementById('btn-ludo-switch')?.addEventListener('click', () => {
      SwitchGameModal.open(this.roomCode, AppState.participantToken);
    });

    document.getElementById('btn-ludo-room')?.addEventListener('click', () => {
      this.returnToRoom();
    });

    document.getElementById('btn-ludo-restart')?.addEventListener('click', () => {
      this.triggerRestart();
    });

    document.getElementById('btn-ludo-leave')?.addEventListener('click', () => {
      this.leaveMatch();
    });

    // Socket listeners
    const onGameUpdate = (data) => {
      if (data.room_code === this.roomCode) {
        const diceFaceEl = document.getElementById('ludo-dice-face');
        diceFaceEl?.classList.remove('rolling');
        this.gameState = data.game_state;
        this.stateVersion = data.state_version;
        this.renderGame();
        if (data.event?.kicked) {
          Toast.info(`💥 Đã ĐÁ ngựa của đối thủ về chuồng!`);
        }
      }
    };

    const onGameRestarted = (data) => {
      if (data.room_code === this.roomCode) {
        Toast.success('Cả hai đã đồng ý! Ván đấu bắt đầu lại!');
        if (data.session_scores && AppState.currentRoom) {
          AppState.currentRoom.session_scores = data.session_scores;
        }
        const btn = document.getElementById('btn-ludo-restart');
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
        const btn = document.getElementById('btn-ludo-restart');
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
      boardEl?.removeEventListener('click', handleHorseClick);
      ApiService.off('game_update', onGameUpdate);
      ApiService.off('game_restarted', onGameRestarted);
      ApiService.off('rematch_requested', onRematchRequested);
      ApiService.off('rematch_declined', onRematchDeclined);
      ApiService.off('room_game_changed', onRoomGameChanged);
      ApiService.off('room_returned_to_lobby', onRoomReturnedToLobby);
    };
  }
}
