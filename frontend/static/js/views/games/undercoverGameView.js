import { AppState } from '../../state.js';
import { Router } from '../../router.js';
import { Toast } from '../../components/toast.js';
import { Modal } from '../../components/modal.js';
import { ApiService } from '../../api.js';
import { SwitchGameModal } from '../../components/switchGameModal.js';
import { RoomChat } from '../../components/roomChat.js';
import { LeaveRoomHelper } from '../../components/leaveRoomHelper.js';

export class UndercoverGameView {
  static currentCleanup = null;
  static gameState = null;
  static stateVersion = 0;
  static isLocal = false;
  static roomCode = null;
  static isSecretVisible = true; // Default visible for the player themselves
  static savedWord = null;
  static savedRole = null;
  static selectedVoteTarget = null;
  static timerInterval = null;
  static timeLeft = 60;
  static gameOverModalShown = false;

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

      // Cache my word & role from initial payload if available
      this.cacheMySecret(res.room.game_state);
    } catch (e) {
      console.error(e);
      Toast.error('Không thể tải ván Undercover');
      return;
    }

    // Initialize in-room chat
    RoomChat.init();
    RoomChat.setRoom(roomCode, AppState.participantToken, this.isLocal);

    // Join socket if online
    if (!this.isLocal) {
      ApiService.joinRoomSocket(roomCode, AppState.participantToken);
    }

    container.innerHTML = `
      <div class="undercover-container">
        <!-- Undercover Header -->
        <div class="undercover-header">
          <div class="undercover-header-left">
            <div class="undercover-game-title">
              <span>🕵️ Undercover</span>
              <span class="undercover-badge-topic" id="uc-topic-badge">Chủ đề: Đang tải</span>
            </div>
            <span class="match-mode-badge">${this.isLocal ? '💻 Local Hotseat' : `🌐 Phòng: ${roomCode}`}</span>
          </div>

          <div class="undercover-header-right">
            <div class="undercover-round-pill" id="uc-round-pill">Vòng 1</div>
            <div class="undercover-phase-pill" id="uc-phase-pill">Mô tả</div>
            
            <button class="btn btn-secondary btn-sm" id="btn-uc-rules">📖 Luật</button>
            <button class="btn btn-secondary btn-sm" id="btn-uc-switch">🎮 Đổi Trò</button>
            <button class="btn btn-sunset btn-sm" id="btn-uc-lobby">🏠 Về Phòng</button>
            <button class="btn btn-ghost btn-sm" id="btn-uc-leave">🚪 Rời Bàn</button>
          </div>
        </div>

        <!-- Spectator Banner (if viewer is spectator) -->
        <div id="uc-spectator-banner" class="undercover-spectator-banner" style="display: none;">
          <span>👁️ Bạn đang theo dõi trận đấu với tư cách <strong>Khán Giả</strong> (Không thấy từ khóa bí mật cho đến khi ván đấu kết thúc).</span>
        </div>

        <!-- My Secret Word Banner (Matching Image 2: "Ví dụ từ được nhận là: con bồ nông") -->
        <div id="uc-my-secret-banner" class="undercover-my-secret-banner" style="display: none;">
          <div style="display: flex; align-items: center; gap: 0.85rem; flex-wrap: wrap;">
            <span class="uc-secret-tag">🔒 TỪ BÍ MẬT CỦA BẠN:</span>
            <span class="uc-secret-main-word" id="uc-secret-word-text">•••••••••••••</span>
            <span class="uc-secret-role-tag" id="uc-secret-role-text">Dân thường</span>
          </div>
          <button class="btn btn-ghost btn-sm" id="btn-toggle-secret-privacy" style="border: 1px solid var(--surface-glass-border-bright); border-radius: var(--radius-full);">
            🙈 Ẩn từ
          </button>
        </div>

        <!-- Turn Notice & Input Action Bar -->
        <!-- 1. My Turn to Describe -->
        <div id="uc-my-turn-bar" class="undercover-active-my-turn-bar" style="display: none;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
            <span style="font-weight: 800; color: var(--color-sunset-orange); font-size: 1rem;">
              ✍️ Đến lượt bạn mô tả! Nhập 1 câu hoặc 1 từ gợi ý về từ khóa của mình:
            </span>
            <span class="undercover-timer-badge" id="uc-my-turn-timer">⏱️ 60s</span>
          </div>
          <div style="display: flex; gap: 0.6rem;">
            <input type="text" id="uc-desc-input" class="form-input" style="flex: 1; padding: 0.65rem 1rem; border-radius: var(--radius-full); font-size: 0.95rem;" placeholder="Nhập mô tả của bạn (ví dụ: '1 - biết bay', '2 - ăn cá')... (Enter để gửi)" maxlength="150" autocomplete="off" />
            <button id="btn-uc-submit-desc" class="btn btn-primary" style="padding: 0.65rem 1.4rem; border-radius: var(--radius-full);">Gửi</button>
            <button id="btn-uc-pass-desc" class="btn btn-ghost btn-sm" style="border-radius: var(--radius-full);">Bỏ lượt</button>
          </div>
        </div>

        <!-- 2. Waiting Other Player to Describe -->
        <div id="uc-waiting-turn-bar" class="undercover-waiting-turn-bar" style="display: none;">
          <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.3rem;">🎙️</span>
            <span>Đang đến lượt <strong id="uc-speaker-name" style="color: var(--color-sunset-orange);">Người chơi</strong> mô tả từ khóa...</span>
          </div>
          <span class="undercover-timer-badge" id="uc-speaker-timer">⏱️ 60s</span>
        </div>

        <!-- 3. Voting Phase Banner -->
        <div id="uc-vote-status-bar" class="undercover-vote-status-bar" style="display: none;">
          <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.4rem;">🗳️</span>
            <div>
              <strong style="color: #FC8181; font-size: 1rem; display: block;">GIAI ĐOẠN BỎ PHIẾU LOẠI GIÁN ĐIỆP</strong>
              <span style="font-size: 0.85rem; color: var(--color-cream-soft);" id="uc-vote-instruction">
                Hãy đọc các mô tả bên dưới và bấm nút "Bỏ Phiếu" vào người bạn nghi ngờ nhất!
              </span>
            </div>
          </div>
          <span class="undercover-timer-badge" id="uc-vote-timer">⏱️ 45s</span>
        </div>

        <!-- Players Columns Grid (Matching Image 2: Column per Player) -->
        <div class="undercover-players-columns-grid" id="uc-columns-grid">
          <!-- Dynamically populated columns -->
        </div>

        <!-- Mr. White Guess Modal -->
        <div id="uc-mrwhite-modal" class="undercover-mrwhite-modal" style="display: none;">
          <div class="undercover-mrwhite-content">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🕵️‍♂️⚪</div>
            <h3 style="color: #FFD700; margin-bottom: 0.5rem;">CƠ HỘI DUY NHẤT CỦA MŨ TRẮNG!</h3>
            <p id="uc-mrwhite-desc" style="color: var(--color-cream-soft); margin-bottom: 1rem; font-size: 0.95rem;">
              Bạn đã bị loại khỏi ván đấu. Nhưng nếu bạn đoán đúng chính xác từ khóa của Dân thường, bạn sẽ <strong>THẮNG NGAY LẬP TỨC!</strong>
            </p>
            <div class="undercover-mrwhite-input-row" id="uc-mrwhite-input-container">
              <input type="text" id="uc-mrwhite-guess-input" class="undercover-mrwhite-input" placeholder="Nhập từ khóa của Dân thường..." maxlength="60" autocomplete="off" />
              <button id="btn-uc-mrwhite-submit" class="btn btn-sunset" style="padding: 0.75rem 1.5rem; font-weight: 800;">Nộp Đáp Án</button>
            </div>
            <div id="uc-mrwhite-waiting" style="display: none; color: var(--color-dusty-rose); font-style: italic; margin-top: 1rem;">
              Đang đợi Mũ Trắng suy đoán từ khóa Dân thường...
            </div>
          </div>
        </div>

        <!-- Game Over Modal Overlay -->
        <div id="uc-gameover-overlay" class="undercover-gameover-overlay" style="display: none;">
          <div class="undercover-gameover-card">
            <div class="undercover-gameover-icon" id="uc-winner-icon">🏆</div>
            <h2 class="undercover-winner-title" id="uc-winner-title">KẾT THÚC VÁN ĐẤU</h2>
            <div class="undercover-winner-desc" id="uc-winner-reason">Chi tiết kết quả trận đấu</div>

            <div class="undercover-reveal-section">
              <div style="font-weight: 800; color: var(--color-dusty-rose); margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.85rem;">Tổng kết vai trò & từ khóa:</div>
              <table class="undercover-reveal-table">
                <thead>
                  <tr>
                    <th>Người chơi</th>
                    <th>Vai trò</th>
                    <th>Từ khóa</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody id="uc-reveal-tbody">
                  <!-- Dynamically populated -->
                </tbody>
              </table>
            </div>

            <div class="undercover-gameover-actions">
              <button id="btn-uc-rematch" class="btn-gameover-action btn-gameover-rematch">🔄 Yêu Cầu Tái Đấu</button>
              <button id="btn-uc-return-lobby" class="btn-gameover-action btn-gameover-lobby">🏠 Về Phòng Chờ</button>
              <button id="btn-uc-return-home" class="btn-gameover-action btn-gameover-home">🚪 Về Trang Chủ</button>
            </div>
          </div>
        </div>
      </div>
    `;

    this.attachEvents();
    this.updateUI();

    // Listen to real-time events
    if (!this.isLocal) {
      ApiService.on('game_update', (data) => {
        if (data && data.game_state) {
          this.cacheMySecret(data.game_state);
          this.gameState = data.game_state;
          this.stateVersion = data.state_version || this.stateVersion;
          this.updateUI();
        }
      });

      ApiService.on('game_restarted', (data) => {
        if (data && data.game_state) {
          this.savedWord = null;
          this.savedRole = null;
          this.cacheMySecret(data.game_state);
          this.gameState = data.game_state;
          this.stateVersion = data.state_version || this.stateVersion;
          this.gameOverModalShown = false;
          const overlay = document.getElementById('uc-gameover-overlay');
          if (overlay) overlay.style.display = 'none';
          Toast.success('Ván đấu mới đã bắt đầu!');
          this.updateUI();
        }
      });

      ApiService.on('room_sync', (room) => {
        if (room) {
          AppState.setRoom(room);
          if (room.game_state) {
            this.cacheMySecret(room.game_state);
            this.gameState = room.game_state;
            this.updateUI();
          }
        }
      });
    }
  }

  static cacheMySecret(state) {
    if (!state) return;
    const myIdx = AppState.playerIndex;

    // Check root level fields
    if (state.my_word && state.my_word !== '???') {
      this.savedWord = state.my_word;
    }
    if (state.my_role && state.my_role !== '???') {
      this.savedRole = state.my_role;
    }

    // Check players array
    const me = state.players?.find(p => p.player_index === myIdx);
    if (me) {
      if (me.word && me.word !== '???') this.savedWord = me.word;
      if (me.role && me.role !== '???') this.savedRole = me.role;
    }
  }

  static updateUI() {
    if (!this.gameState) return;
    const s = this.gameState;
    const room = AppState.currentRoom;
    const isSpectator = room?.is_viewer_spectator || (AppState.playerIndex === null || AppState.playerIndex === undefined);

    // Topic badge
    const topicEl = document.getElementById('uc-topic-badge');
    if (topicEl) {
      const catName = s.word_pair_info?.category_name || s.settings?.topic || 'Ngẫu nhiên';
      topicEl.textContent = `Chủ đề: ${catName}`;
    }

    // Round pill
    const roundEl = document.getElementById('uc-round-pill');
    if (roundEl) {
      roundEl.textContent = `Vòng ${s.round_number || 1}`;
    }

    // Phase pill
    const phaseEl = document.getElementById('uc-phase-pill');
    if (phaseEl) {
      phaseEl.className = `undercover-phase-pill ${s.phase}`;
      const phaseNames = {
        describe: 'Mô tả',
        vote: 'Bỏ phiếu',
        mrwhite_guess: 'Mũ Trắng đoán',
        finished: 'Kết thúc'
      };
      phaseEl.textContent = phaseNames[s.phase] || s.phase;
    }

    // Spectator banner vs Secret word banner
    const specBanner = document.getElementById('uc-spectator-banner');
    const secretBanner = document.getElementById('uc-my-secret-banner');
    if (specBanner && secretBanner) {
      if (isSpectator) {
        specBanner.style.display = 'flex';
        secretBanner.style.display = 'none';
      } else {
        specBanner.style.display = 'none';
        secretBanner.style.display = 'flex';
        this.renderSecretBanner();
      }
    }

    // Render Action Bars (My Turn, Waiting, Vote)
    this.renderActionBars();

    // Render Columns Grid (Matching Image 2)
    this.renderColumnsGrid();

    // Mr White Guess Modal
    this.renderMrWhiteModal();

    // Game Over
    if (s.phase === 'finished') {
      this.showGameOverModal();
    }
  }

  static renderSecretBanner() {
    const wordTextEl = document.getElementById('uc-secret-word-text');
    const roleTextEl = document.getElementById('uc-secret-role-text');
    const btnToggle = document.getElementById('btn-toggle-secret-privacy');
    if (!wordTextEl || !roleTextEl || !btnToggle) return;

    const myIdx = AppState.playerIndex;
    const me = this.gameState.players?.find(p => p.player_index === myIdx);
    const role = this.savedRole || me?.role || 'civilian';
    const word = this.savedWord || me?.word || '';

    const roleNames = {
      civilian: 'Dân thường',
      undercover: 'Mũ Đen (Undercover)',
      mr_white: 'Mũ Trắng (Mr. White)'
    };

    roleTextEl.className = `uc-secret-role-tag ${role}`;
    roleTextEl.textContent = roleNames[role] || role;

    if (this.isSecretVisible) {
      btnToggle.textContent = '🙈 Ẩn từ';
      if (role === 'mr_white') {
        wordTextEl.textContent = 'Bạn là Mũ Trắng (Không có từ khóa)';
        wordTextEl.style.fontSize = '1.15rem';
        wordTextEl.style.color = '#FFD700';
      } else {
        wordTextEl.textContent = word || 'Đang lấy từ...';
        wordTextEl.style.fontSize = '1.6rem';
        wordTextEl.style.color = 'var(--color-sunset-orange)';
      }
    } else {
      btnToggle.textContent = '👁️ Hiện từ';
      wordTextEl.textContent = '•••••••••••••';
      wordTextEl.style.fontSize = '1.3rem';
      wordTextEl.style.color = 'rgba(255, 225, 186, 0.5)';
    }
  }

  static renderActionBars() {
    const s = this.gameState;
    const myIdx = AppState.playerIndex;
    const myTurnBar = document.getElementById('uc-my-turn-bar');
    const waitingBar = document.getElementById('uc-waiting-turn-bar');
    const voteBar = document.getElementById('uc-vote-status-bar');
    const speakerNameEl = document.getElementById('uc-speaker-name');

    if (!myTurnBar || !waitingBar || !voteBar) return;

    if (s.phase === 'describe') {
      voteBar.style.display = 'none';
      const isMyTurn = (this.isLocal || s.current_player === myIdx);

      if (isMyTurn) {
        myTurnBar.style.display = 'block';
        waitingBar.style.display = 'none';
        const input = document.getElementById('uc-desc-input');
        input?.focus();
      } else {
        myTurnBar.style.display = 'none';
        waitingBar.style.display = 'flex';
        const speaker = s.players?.find(p => p.player_index === s.current_player);
        if (speakerNameEl) {
          speakerNameEl.textContent = speaker ? speaker.name : 'Người chơi';
        }
      }
    } else if (s.phase === 'vote') {
      myTurnBar.style.display = 'none';
      waitingBar.style.display = 'none';
      voteBar.style.display = 'flex';
      const revoteInfo = document.getElementById('uc-vote-instruction');
      if (revoteInfo) {
        if (s.is_revote) {
          revoteInfo.innerHTML = '<strong style="color: #FFD700;">HÒA PHIẾU!</strong> Đang bỏ phiếu lại giữa các người chơi hòa điểm. Hãy chọn 1 người!';
        } else {
          revoteInfo.textContent = 'Hãy đọc lại các mô tả trong từng cột bên dưới và bấm nút "Bỏ Phiếu" vào người bạn nghi ngờ nhất!';
        }
      }
    } else {
      myTurnBar.style.display = 'none';
      waitingBar.style.display = 'none';
      voteBar.style.display = 'none';
    }
  }

  static renderColumnsGrid() {
    const grid = document.getElementById('uc-columns-grid');
    if (!grid) return;

    const s = this.gameState;
    const players = s.players || [];
    const myIdx = AppState.playerIndex;
    const isVotePhase = (s.phase === 'vote');
    const isViewerAlive = players.some(p => p.player_index === myIdx && p.is_alive);
    const myVoteTarget = s.votes?.[String(myIdx)]?.target ?? (s.votes?.[String(myIdx)] === undefined ? null : s.votes[String(myIdx)]);

    const allDescriptions = s.descriptions || {};

    grid.innerHTML = players.map(p => {
      const isSpeaking = (s.phase === 'describe' && s.current_player === p.player_index);
      const isElim = !p.is_alive;
      const isMe = (p.player_index === myIdx);
      const initial = p.name ? p.name.charAt(0).toUpperCase() : '?';

      // Collect descriptions for this player across all rounds
      const descs = [];
      Object.keys(allDescriptions).sort((a, b) => parseInt(a) - parseInt(b)).forEach(rndKey => {
        const roundList = allDescriptions[rndKey] || [];
        const item = roundList.find(d => d.player_index === p.player_index);
        if (item) {
          descs.push({ round: rndKey, text: item.text, passed: item.passed });
        }
      });

      // Vote count badge if tally is in
      let voteCountBadge = '';
      if (s.vote_tallies && s.vote_tallies[String(p.player_index)] !== undefined) {
        voteCountBadge = `<span class="status-badge votes">${s.vote_tallies[String(p.player_index)]} phiếu</span>`;
      }

      // Check voting button eligibility
      const canVoteThis = isVotePhase && isViewerAlive && p.is_alive && (!s.is_revote || s.revote_candidates?.includes(p.player_index));
      const hasVotedForThis = (this.selectedVoteTarget === p.player_index || myVoteTarget === p.player_index);

      return `
        <div class="undercover-column-card ${isSpeaking ? 'is-speaking' : ''} ${isElim ? 'is-eliminated' : ''} ${isMe ? 'is-me' : ''}">
          <div class="column-card-header" style="border-bottom: 2px solid ${p.color || 'var(--color-sunset-orange)'};">
            <div class="column-player-avatar" style="background: ${p.color || 'var(--color-sunset-orange)'};">
              ${initial}
            </div>
            <div class="column-player-info">
              <div class="column-player-name" title="${this.escape(p.name)}">
                ${p.is_host ? '👑 ' : ''}${this.escape(p.name)}${isMe ? ' (Bạn)' : ''}
              </div>
              <div class="column-player-status">
                ${isElim ? '<span class="status-badge eliminated">ĐÃ BỊ LOẠI</span>' : (isSpeaking ? '<span class="status-badge speaking">🎙️ Đang nói...</span>' : '<span class="status-badge alive">Còn sống</span>')}
                ${voteCountBadge}
              </div>
            </div>
          </div>

          <!-- Body: List of Descriptions across rounds (Matching Image 2: "1 - biết bay", "2 - ăn cá") -->
          <div class="column-card-body">
            ${descs.length > 0 ? descs.map(d => `
              <div class="column-desc-item">
                <span class="desc-round-num">${d.round} -</span>
                <span class="desc-text" style="${d.passed ? 'font-style: italic; color: #BE807D;' : ''}">${this.escape(d.text)}</span>
              </div>
            `).join('') : `
              <div style="color: var(--color-dusty-rose); font-style: italic; font-size: 0.82rem; padding: 0.5rem; text-align: center;">
                Chưa có mô tả nào
              </div>
            `}
          </div>

          <!-- Footer: Voting button in Vote Phase -->
          ${canVoteThis ? `
            <div class="column-card-footer">
              <button class="btn ${hasVotedForThis ? 'btn-success' : 'btn-sunset'} btn-sm btn-vote-candidate" data-target="${p.player_index}" style="width: 100%; border-radius: var(--radius-full);">
                ${hasVotedForThis ? '✓ Bạn đã chọn' : '🗳️ Bỏ Phiếu Loại'}
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');

    // Attach click listener for voting buttons
    grid.querySelectorAll('.btn-vote-candidate').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const targetIdx = parseInt(e.target.dataset.target, 10);
        this.selectedVoteTarget = targetIdx;
        this.executeAction({
          type: 'submit_vote',
          target_player_index: targetIdx
        });
        Toast.info('Đã gửi phiếu bầu của bạn!');
      });
    });
  }

  static renderMrWhiteModal() {
    const s = this.gameState;
    const modal = document.getElementById('uc-mrwhite-modal');
    const inputContainer = document.getElementById('uc-mrwhite-input-container');
    const waitingContainer = document.getElementById('uc-mrwhite-waiting');

    if (!modal) return;

    if (s.phase === 'mrwhite_guess' && s.pending_mrwhite !== null) {
      modal.style.display = 'flex';
      const myIdx = AppState.playerIndex;
      const isPendingWhite = (this.isLocal || myIdx === s.pending_mrwhite);

      if (isPendingWhite) {
        if (inputContainer) inputContainer.style.display = 'flex';
        if (waitingContainer) waitingContainer.style.display = 'none';
        const input = document.getElementById('uc-mrwhite-guess-input');
        input?.focus();
      } else {
        if (inputContainer) inputContainer.style.display = 'none';
        if (waitingContainer) waitingContainer.style.display = 'block';
      }
    } else {
      modal.style.display = 'none';
    }
  }

  static showGameOverModal() {
    if (this.gameOverModalShown) return;
    this.gameOverModalShown = true;

    const s = this.gameState;
    const overlay = document.getElementById('uc-gameover-overlay');
    const iconEl = document.getElementById('uc-winner-icon');
    const titleEl = document.getElementById('uc-winner-title');
    const reasonEl = document.getElementById('uc-winner-reason');
    const tbody = document.getElementById('uc-reveal-tbody');

    if (!overlay || !titleEl || !reasonEl || !tbody) return;

    overlay.style.display = 'flex';

    const winner = s.winner || {};
    const team = winner.team;

    if (team === 'civilian') {
      iconEl.textContent = '🎉🧑‍🌾';
      titleEl.textContent = 'PHE DÂN THƯỜNG CHIẾN THẮNG!';
      titleEl.style.color = '#4FD1C5';
    } else if (team === 'undercover') {
      iconEl.textContent = '🕵️‍♂️🔥';
      titleEl.textContent = 'PHE MŨ ĐEN CHIẾN THẮNG!';
      titleEl.style.color = '#FC8181';
    } else if (team === 'mr_white') {
      iconEl.textContent = '👑⚪';
      titleEl.textContent = 'MŨ TRẮNG CHIẾN THẮNG!';
      titleEl.style.color = '#FFD700';
    } else {
      iconEl.textContent = '🏆';
      titleEl.textContent = 'GIÁN ĐIỆP CHIẾN THẮNG!';
      titleEl.style.color = '#FF9966';
    }

    reasonEl.textContent = winner.reason || 'Trận đấu kết thúc.';

    const roleNames = {
      civilian: 'Dân thường',
      undercover: 'Mũ Đen',
      mr_white: 'Mũ Trắng'
    };

    tbody.innerHTML = (s.players || []).map(p => `
      <tr>
        <td><strong>${this.escape(p.name)}</strong></td>
        <td><span class="badge-undercover-role ${p.role}">${roleNames[p.role] || p.role}</span></td>
        <td style="color: var(--color-sunset-orange); font-weight: 700;">${p.role === 'mr_white' ? '(Không có)' : this.escape(p.word || '---')}</td>
        <td>${p.is_alive ? '<span style="color: #4FD1C5;">Sống sót</span>' : '<span style="color: #FC8181;">Bị loại</span>'}</td>
      </tr>
    `).join('');
  }

  static attachEvents() {
    this.cleanup();

    // Toggle Secret Word Privacy (Show / Hide)
    document.getElementById('btn-toggle-secret-privacy')?.addEventListener('click', () => {
      this.isSecretVisible = !this.isSecretVisible;
      this.renderSecretBanner();
    });

    // Submit Description
    const submitDesc = () => {
      const input = document.getElementById('uc-desc-input');
      const text = (input?.value || '').trim();
      if (!text) {
        Toast.error('Vui lòng nhập mô tả của bạn');
        input?.focus();
        return;
      }
      this.executeAction({
        type: 'submit_description',
        text: text
      });
      if (input) input.value = '';
    };

    document.getElementById('btn-uc-submit-desc')?.addEventListener('click', submitDesc);
    document.getElementById('uc-desc-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitDesc();
      }
    });

    // Pass Description
    document.getElementById('btn-uc-pass-desc')?.addEventListener('click', () => {
      this.executeAction({
        type: 'pass_description'
      });
    });

    // Mr White Guess Submit
    const submitMrWhite = () => {
      const input = document.getElementById('uc-mrwhite-guess-input');
      const guess = (input?.value || '').trim();
      if (!guess) {
        Toast.error('Vui lòng nhập từ khóa bạn suy đoán');
        input?.focus();
        return;
      }
      this.executeAction({
        type: 'mrwhite_guess',
        guess: guess
      });
    };

    document.getElementById('btn-uc-mrwhite-submit')?.addEventListener('click', submitMrWhite);
    document.getElementById('uc-mrwhite-guess-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitMrWhite();
      }
    });

    // Game Over Actions
    document.getElementById('btn-uc-rematch')?.addEventListener('click', () => {
      ApiService.requestRematchSocket(this.roomCode, AppState.participantToken);
      Toast.info('Đã gửi yêu cầu tái đấu!');
    });

    document.getElementById('btn-uc-return-lobby')?.addEventListener('click', () => {
      this.returnToLobby();
    });

    document.getElementById('btn-uc-return-home')?.addEventListener('click', () => {
      this.leaveMatch();
    });

    // Header buttons
    document.getElementById('btn-uc-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: 'undercover' });
    });

    document.getElementById('btn-uc-switch')?.addEventListener('click', () => {
      SwitchGameModal.open(this.roomCode, AppState.participantToken);
    });

    document.getElementById('btn-uc-lobby')?.addEventListener('click', () => {
      this.returnToLobby();
    });

    document.getElementById('btn-uc-leave')?.addEventListener('click', () => {
      this.leaveMatch();
    });
  }

  static returnToLobby() {
    if (this.isLocal) {
      Router.navigate('local_setup', { game: 'undercover' });
    } else {
      if (AppState.isHost) {
        ApiService.returnToLobbySocket(this.roomCode, AppState.participantToken);
      } else {
        Router.navigate('online_lobby', { roomCode: this.roomCode, mode: 'lobby' });
      }
    }
  }

  static leaveMatch() {
    LeaveRoomHelper.promptLeave(this.roomCode, AppState.participantToken, AppState.isHost, this.isLocal);
  }

  static async executeAction(action) {
    if (!this.isLocal && ApiService.socket && ApiService.socket.connected) {
      ApiService.sendActionSocket(this.roomCode, AppState.participantToken, action, this.stateVersion);
    } else {
      try {
        const res = await ApiService.sendActionRest(this.roomCode, AppState.participantToken, action, this.stateVersion);
        if (res.success) {
          this.cacheMySecret(res.room.game_state);
          this.gameState = res.room.game_state;
          this.stateVersion = res.room.state_version;
          this.updateUI();
        } else {
          Toast.error(res.error || 'Lỗi thao tác');
        }
      } catch (err) {
        console.error(err);
        Toast.error('Lỗi khi gửi hành động');
      }
    }
  }

  static cleanup() {
    if (this.currentCleanup) {
      this.currentCleanup();
      this.currentCleanup = null;
    }
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  static escape(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}
