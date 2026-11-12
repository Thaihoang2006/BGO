import { AppState } from '../../state.js';
import { Router } from '../../router.js';
import { Toast } from '../../components/toast.js';
import { Modal } from '../../components/modal.js';
import { ApiService } from '../../api.js';
import { SwitchGameModal } from '../../components/switchGameModal.js';
import { RematchModal } from '../../components/rematchModal.js';
import { LeaveRoomHelper } from '../../components/leaveRoomHelper.js';

export class GemKingdomView {
  static currentCleanup = null;
  static gameState = null;
  static stateVersion = 0;
  static isLocal = false;
  static roomCode = null;
  static selectedGems = []; // For taking 3 gems

  static async render(container, params = {}) {
    const roomCode = params.roomCode || AppState.roomCode;
    if (!roomCode) {
      Router.navigate('home');
      return;
    }

    this.roomCode = roomCode;
    this.selectedGems = [];

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
      <div class="gem-kingdom-container">
        <!-- Match Header -->
        <div class="glass-panel match-header">
          <div class="match-room-info">
            <span class="match-game-title">Gem Kingdom (Splendor)</span>
            <span class="match-mode-badge">${this.isLocal ? '💻 Local (1 Máy)' : `🌐 Phòng: ${roomCode}`}</span>
            <span class="match-mode-badge" id="round-indicator">Vòng 1</span>
          </div>

          <div class="match-controls">
            <button class="btn btn-secondary btn-sm" id="btn-gk-rules">
              📖 Luật Chơi
            </button>
            <button class="btn btn-secondary btn-sm" id="btn-gk-switch">
              🎮 Đổi Trò
            </button>
            <button class="btn btn-sunset btn-sm" id="btn-gk-room">
              🏠 Về Phòng
            </button>
            <button class="btn btn-ghost btn-sm" id="btn-gk-leave">
              🚪 Rời Bàn
            </button>
          </div>
        </div>

        <!-- Turn Banner -->
        <div class="turn-banner" id="gk-turn-banner">
          <div class="turn-indicator-dot" id="gk-turn-dot"></div>
          <div class="turn-text" id="gk-turn-text">Đang tải bàn cờ...</div>
        </div>

        <!-- Main Layout: Board + Sidebar -->
        <div class="gk-game-layout">
          <div class="gk-board-area">
            <!-- Nobles Row -->
            <div style="margin-bottom: 0.5rem; font-size: 0.85rem; font-weight: 700; color: var(--color-dusty-rose); text-transform: uppercase;">
              👑 Các Thẻ Quý Tộc (+3 Điểm)
            </div>
            <div class="nobles-row" id="gk-nobles-row"></div>

            <!-- Development Cards 3 Levels -->
            <div style="margin-bottom: 0.5rem; font-size: 0.85rem; font-weight: 700; color: var(--color-dusty-rose); text-transform: uppercase;">
              🃏 Thẻ Tinh Luyện (Lật Ngửa 12 Thẻ)
            </div>
            <div class="cards-tiers-container" id="gk-cards-tiers"></div>

            <!-- Bank Tokens Section -->
            <div class="glass-panel bank-section">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <span style="font-weight: 700; color: var(--color-cream); font-size: 1rem;">
                  💎 Kho Đá Quý & Token Vàng
                </span>
                <span style="font-size: 0.8rem; color: var(--color-dusty-rose);">
                  Nhấp vào các viên đá quý để chọn hành động lấy token
                </span>
              </div>
              <div class="bank-tokens-grid" id="gk-bank-grid"></div>
              <div class="token-action-bar" id="gk-token-action-bar"></div>
            </div>
          </div>

          <!-- Players Sidebar -->
          <div class="gk-sidebar" id="gk-players-sidebar"></div>
        </div>
      </div>
    `;

    this.renderGame();
    this.attachEvents();
  }

  static renderGame() {
    if (!this.gameState) return;

    this.updateTurnBanner();
    this.renderNobles();
    this.renderCards();
    this.renderBank();
    this.renderPlayersSidebar();
  }

  static isMyTurn() {
    if (!this.gameState || this.gameState.status !== 'playing') return false;
    if (this.isLocal) return true;
    return AppState.playerIndex === this.gameState.current_player;
  }

  static updateTurnBanner() {
    const banner = document.getElementById('gk-turn-banner');
    const text = document.getElementById('gk-turn-text');
    const dot = document.getElementById('gk-turn-dot');
    const roundInd = document.getElementById('round-indicator');

    if (roundInd) {
      roundInd.textContent = `Vòng ${this.gameState.round_number || 1}${this.gameState.final_round_triggered ? ' (VÒNG CUỐI!)' : ''}`;
    }

    const currIdx = this.gameState.current_player;
    const player = this.gameState.players[currIdx];

    if (this.gameState.status === 'finished') {
      const winner = this.gameState.winner;
      text.innerHTML = `🏆 <strong>${winner.name}</strong> chiến thắng với <strong>${winner.prestige_points} điểm</strong> (${winner.cards_count} thẻ tinh luyện)!`;
      if (dot) dot.style.background = 'var(--color-success)';
      banner?.classList.remove('active-turn-glow');
      if (!this.gameOverModalShown) {
        this.gameOverModalShown = true;
        this.showGameOverModal(winner);
      }
    } else {
      this.gameOverModalShown = false;
      if (this.gameState.pending_discard_player !== null && this.gameState.pending_discard_player !== undefined) {
      const pDiscard = this.gameState.players[this.gameState.pending_discard_player];
      text.innerHTML = `⚠️ <strong>${pDiscard.name}</strong> đang có hơn 10 token! Hãy trả bớt token dư thừa.`;
      if (dot) dot.style.background = 'var(--color-danger)';
      banner?.classList.add('active-turn-glow');
      if (this.isLocal || AppState.playerIndex === this.gameState.pending_discard_player) {
        this.showDiscardModal(pDiscard);
      }
    } else {
      const isMine = this.isMyTurn();
      if (this.isLocal) {
        text.innerHTML = `Lượt đi của: <strong style="color: ${player.color};">${player.name}</strong> (${player.prestige_points} điểm)`;
      } else {
        if (isMine) {
          text.innerHTML = `✨ <strong>Lượt của BẠN!</strong> Chọn lấy đá quý, mua thẻ hoặc dự trữ thẻ`;
        } else {
          text.innerHTML = `⏳ Đang đợi <strong>${player.name}</strong> thực hiện lượt đi...`;
        }
      }
      if (dot) dot.style.background = player.color || 'var(--color-sunset-orange)';
      banner?.classList.add('active-turn-glow');
    }
  }
}

  static renderNobles() {
    const row = document.getElementById('gk-nobles-row');
    if (!row || !this.gameState.nobles) return;

    row.innerHTML = this.gameState.nobles.map(n => `
      <div class="noble-tile">
        <div class="noble-header">
          <span class="noble-points">⭐ ${n.points}</span>
          <span class="noble-name">${n.name}</span>
        </div>
        <div class="noble-requires">
          ${Object.entries(n.requires).map(([gem, count]) => `
            <div class="noble-req-badge gem-${gem}">${count}</div>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  static renderCards() {
    const container = document.getElementById('gk-cards-tiers');
    if (!container || !this.gameState.board) return;

    const activePlayer = this.gameState.players[this.gameState.current_player];
    const canInteract = this.isMyTurn();

    container.innerHTML = ['3', '2', '1'].map(lvl => {
      const cards = this.gameState.board[lvl] || [];
      const deckCount = this.gameState.decks_count ? this.gameState.decks_count[lvl] : 0;

      return `
        <div class="cards-tier-row">
          <!-- Deck -->
          <div class="deck-card deck-level-${lvl}" data-action="reserve_deck" data-level="${lvl}">
            <div class="deck-title">Cấp ${lvl}</div>
            <div class="deck-count">${deckCount} lá</div>
            <span style="font-size: 0.65rem; color: var(--color-cream-soft); margin-top: 0.2rem;">Dự trữ bí mật</span>
          </div>

          <!-- 4 Cards -->
          ${cards.map(card => {
            const canAfford = canInteract && this.canPlayerAfford(activePlayer, card);
            return `
              <div class="dev-card ${canAfford ? 'can-afford' : ''}" data-action="card_click" data-card-id="${card.id}" data-level="${lvl}">
                <div class="dev-card-header">
                  <span class="card-prestige">${card.points > 0 ? card.points : ''}</span>
                  <div class="card-bonus-gem gem-${card.gem}"></div>
                </div>

                <div class="dev-card-costs">
                  ${Object.entries(card.cost || {}).map(([g, cost]) => `
                    <div class="cost-pip gem-${g}">${cost}</div>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }).join('');
  }

  static renderBank() {
    const grid = document.getElementById('gk-bank-grid');
    const actionBar = document.getElementById('gk-token-action-bar');
    if (!grid || !this.gameState.bank) return;

    const bank = this.gameState.bank;
    const allGems = ['emerald', 'diamond', 'sapphire', 'onyx', 'ruby', 'gold'];

    grid.innerHTML = allGems.map(g => {
      const qty = bank[g] || 0;
      const isSelected = this.selectedGems.includes(g);
      const isClickable = g !== 'gold' && qty > 0;

      return `
        <div class="bank-token-slot">
          <div class="gem-token gem-${g} ${isClickable ? 'clickable' : ''} ${isSelected ? 'selected' : ''}" data-gem="${g}">
            ${g === 'gold' ? '★' : ''}
          </div>
          <span class="bank-token-qty">${qty}</span>
        </div>
      `;
    }).join('');

    // Action bar for token taking
    if (!actionBar) return;
    if (this.selectedGems.length === 0) {
      actionBar.innerHTML = `<span style="font-size: 0.85rem; color: var(--color-dusty-rose);">Chọn 3 viên khác màu hoặc 1 viên (có số lượng ≥ 4) để thực hiện hành động</span>`;
    } else if (this.selectedGems.length === 1) {
      const singleGem = this.selectedGems[0];
      const canTakeTwo = bank[singleGem] >= 4;
      actionBar.innerHTML = `
        <button class="btn btn-sunset btn-sm" id="btn-take-two" ${!canTakeTwo ? 'disabled style="opacity: 0.4;"' : ''}>
          Lấy 2 Viên ${singleGem.toUpperCase()} ${!canTakeTwo ? '(Cần ≥ 4 viên trong kho)' : ''}
        </button>
        <button class="btn btn-ghost btn-sm" id="btn-clear-selection">Bỏ chọn</button>
      `;
    } else {
      actionBar.innerHTML = `
        <button class="btn btn-primary btn-sm" id="btn-take-three">
          Lấy ${this.selectedGems.length} Viên Đã Chọn (${this.selectedGems.join(', ')})
        </button>
        <button class="btn btn-ghost btn-sm" id="btn-clear-selection">Bỏ chọn</button>
      `;
    }
  }

  static renderPlayersSidebar() {
    const sidebar = document.getElementById('gk-players-sidebar');
    if (!sidebar || !this.gameState.players) return;

    const players = this.gameState.players;
    const currIdx = this.gameState.current_player;

    sidebar.innerHTML = players.map(p => {
      const isActive = p.player_index === currIdx && this.gameState.status === 'playing';
      const totalTokens = Object.values(p.tokens).reduce((a, b) => a + b, 0);

      return `
        <div class="player-panel ${isActive ? 'is-active-turn' : ''}">
          <div class="player-panel-header">
            <div class="player-name-points">
              <h4>${p.name} ${p.player_index === 0 ? '<span style="font-size: 0.72rem; color: var(--color-sunset-orange);">(Đi trước)</span>' : ''}</h4>
            </div>
            <div class="player-prestige-badge">
              ⭐ ${p.prestige_points}
            </div>
          </div>

          <div class="player-resources-summary">
            <!-- Tokens -->
            <div class="resource-row">
              <span class="resource-label">Tokens (${totalTokens}/10):</span>
              ${Object.entries(p.tokens).filter(([_, qty]) => qty > 0).map(([g, qty]) => `
                <div class="mini-gem-chip gem-${g}">${g === 'gold' ? '★ ' : ''}${qty}</div>
              `).join('') || '<span style="font-size:0.75rem; color:var(--color-dusty-rose);">0</span>'}
            </div>

            <!-- Permanent Bonuses (Discounts) -->
            <div class="resource-row">
              <span class="resource-label">Giảm giá:</span>
              ${Object.entries(p.bonuses).filter(([_, qty]) => qty > 0).map(([g, qty]) => `
                <div class="mini-gem-chip gem-${g}">+${qty}</div>
              `).join('') || '<span style="font-size:0.75rem; color:var(--color-dusty-rose);">0</span>'}
            </div>

            <!-- Nobles -->
            ${p.nobles && p.nobles.length > 0 ? `
              <div class="resource-row">
                <span class="resource-label">Quý tộc:</span>
                ${p.nobles.map(n => `<span style="font-size: 0.78rem; color: #f1c40f;">👑 ${n.name} (+3)</span>`).join(', ')}
              </div>
            ` : ''}

            <!-- Reserved Cards -->
            ${p.reserved_cards && p.reserved_cards.length > 0 ? `
              <div class="reserved-cards-preview">
                <span style="font-size: 0.75rem; font-weight: 700; color: var(--color-sunset-orange);">
                  Bài Dự Trữ (${p.reserved_cards.length}/3):
                </span>
                <div>
                  ${p.reserved_cards.map(c => `
                    <div class="reserved-card-chip" data-action="buy_reserved" data-card-id="${c.id}">
                      <div class="card-bonus-gem gem-${c.gem}" style="width:14px; height:14px;"></div>
                      <span>${c.points > 0 ? c.points + '★' : '0★'}</span>
                      <span style="font-size: 0.7rem; color: var(--color-success);">Mua</span>
                    </div>
                  `).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  static canPlayerAfford(player, card) {
    let goldNeeded = 0;
    for (const [gem, cost] of Object.entries(card.cost || {})) {
      const bonus = player.bonuses[gem] || 0;
      const net = Math.max(0, cost - bonus);
      const tokens = player.tokens[gem] || 0;
      if (tokens < net) {
        goldNeeded += (net - tokens);
      }
    }
    return (player.tokens.gold || 0) >= goldNeeded;
  }

  static cleanup() {
    if (this.currentCleanup) {
      this.currentCleanup();
      this.currentCleanup = null;
    }
  }

  static attachEvents() {
    this.cleanup();

    // Top control buttons
    document.getElementById('btn-gk-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: 'gem_kingdom' });
    });

    document.getElementById('btn-gk-switch')?.addEventListener('click', () => {
      SwitchGameModal.open(this.roomCode, AppState.participantToken);
    });

    document.getElementById('btn-gk-room')?.addEventListener('click', () => {
      this.returnToRoom();
    });

    document.getElementById('btn-gk-restart')?.addEventListener('click', () => {
      this.triggerRestart();
    });

    document.getElementById('btn-gk-leave')?.addEventListener('click', () => {
      this.leaveMatch();
    });

    // Bank tokens click
    const bankGrid = document.getElementById('gk-bank-grid');
    const handleBankClick = (e) => {
      const token = e.target.closest('.gem-token.clickable');
      if (!token) return;
      const gem = token.dataset.gem;
      if (gem === 'gold') return;

      const idx = this.selectedGems.indexOf(gem);
      if (idx >= 0) {
        this.selectedGems.splice(idx, 1);
      } else {
        if (this.selectedGems.length >= 3) {
          this.selectedGems.shift(); // keep max 3
        }
        this.selectedGems.push(gem);
      }
      this.renderBank();
    };
    bankGrid?.addEventListener('click', handleBankClick);

    // Action bar buttons delegation
    const actionBar = document.getElementById('gk-token-action-bar');
    const handleActionBarClick = (e) => {
      if (e.target.id === 'btn-clear-selection') {
        this.selectedGems = [];
        this.renderBank();
      } else if (e.target.id === 'btn-take-two') {
        if (this.selectedGems.length === 1) {
          this.sendAction({
            type: 'take_two_gems',
            gem: this.selectedGems[0]
          });
          this.selectedGems = [];
        }
      } else if (e.target.id === 'btn-take-three') {
        if (this.selectedGems.length > 0) {
          this.sendAction({
            type: 'take_three_gems',
            gems: [...this.selectedGems]
          });
          this.selectedGems = [];
        }
      }
    };
    actionBar?.addEventListener('click', handleActionBarClick);

    // Cards click handling
    const tiersContainer = document.getElementById('gk-cards-tiers');
    const handleCardsClick = (e) => {
      const cardEl = e.target.closest('.dev-card');
      const deckEl = e.target.closest('.deck-card');

      if (cardEl) {
        const cardId = cardEl.dataset.cardId;
        const level = cardEl.dataset.level;
        this.showCardActionDialog(cardId, level);
      } else if (deckEl) {
        const level = deckEl.dataset.level;
        if (confirm(`Bạn có muốn dự trữ bí mật 1 lá từ đỉnh chồng bài Cấp ${level} và nhận 1 token Vàng không?`)) {
          this.sendAction({
            type: 'reserve_card',
            source: 'deck',
            level: level
          });
        }
      }
    };
    tiersContainer?.addEventListener('click', handleCardsClick);

    // Reserved cards click
    const sidebar = document.getElementById('gk-players-sidebar');
    const handleSidebarClick = (e) => {
      const chip = e.target.closest('.reserved-card-chip');
      if (chip) {
        const cardId = chip.dataset.cardId;
        this.sendAction({
          type: 'buy_card',
          source: 'reserved',
          card_id: cardId
        });
      }
    };
    sidebar?.addEventListener('click', handleSidebarClick);

    // Socket events
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
        const btn = document.getElementById('btn-gk-restart');
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
        const btn = document.getElementById('btn-gk-restart');
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
      bankGrid?.removeEventListener('click', handleBankClick);
      actionBar?.removeEventListener('click', handleActionBarClick);
      tiersContainer?.removeEventListener('click', handleCardsClick);
      sidebar?.removeEventListener('click', handleSidebarClick);
      ApiService.off('game_update', onGameUpdate);
      ApiService.off('game_restarted', onGameRestarted);
      ApiService.off('rematch_requested', onRematchRequested);
      ApiService.off('rematch_declined', onRematchDeclined);
      ApiService.off('room_game_changed', onRoomGameChanged);
      ApiService.off('room_returned_to_lobby', onRoomReturnedToLobby);
    };
  }

  static showCardActionDialog(cardId, level) {
    if (!this.gameState) return;

    let targetCard = null;
    for (const lvl of ['1', '2', '3']) {
      for (const c of this.gameState.board[lvl]) {
        if (c.id === cardId) {
          targetCard = c;
          break;
        }
      }
    }
    if (!targetCard) return;

    const activePlayer = this.gameState.players[this.gameState.current_player];
    const canAfford = this.canPlayerAfford(activePlayer, targetCard);
    const canReserve = activePlayer.reserved_cards.length < 3;

    const modalHtml = `
      <div style="text-align: center; padding: 1rem 0;">
        <div style="display: inline-flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
          <div class="gem-token gem-${targetCard.gem}"></div>
          <div style="text-align: left;">
            <h3 style="color: var(--color-cream); font-size: 1.3rem;">Thẻ Tinh Luyện Cấp ${targetCard.level}</h3>
            <span style="color: var(--color-sunset-orange); font-weight: 700;">Điểm uy tín: ⭐ ${targetCard.points}</span>
          </div>
        </div>

        <div style="background: rgba(25, 14, 21, 0.5); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem;">
          <span style="font-size: 0.85rem; color: var(--color-dusty-rose); display: block; margin-bottom: 0.5rem;">Chi phí mua thẻ:</span>
          <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;">
            ${Object.entries(targetCard.cost || {}).map(([g, cost]) => `
              <div class="mini-gem-chip gem-${g}">${cost} ${g.toUpperCase()}</div>
            `).join('')}
          </div>
        </div>

        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
          <button class="btn btn-primary btn-lg" id="modal-btn-buy" ${!canAfford ? 'disabled style="opacity: 0.4;"' : ''}>
            <span>🛒</span> Mua Thẻ Này ${!canAfford ? '(Thiếu tài nguyên)' : ''}
          </button>
          <button class="btn btn-sunset" id="modal-btn-reserve" ${!canReserve ? 'disabled style="opacity: 0.4;"' : ''}>
            <span>📌</span> Dự Trữ Thẻ (+1 Vàng)
          </button>
        </div>
      </div>
    `;

    Modal.open('Chi Tiết Thẻ Tinh Luyện', modalHtml);

    document.getElementById('modal-btn-buy')?.addEventListener('click', () => {
      Modal.close();
      this.sendAction({
        type: 'buy_card',
        source: 'board',
        card_id: cardId
      });
    });

    document.getElementById('modal-btn-reserve')?.addEventListener('click', () => {
      Modal.close();
      this.sendAction({
        type: 'reserve_card',
        source: 'board',
        level: level,
        card_id: cardId
      });
    });
  }

  static showDiscardModal(player) {
    const totalTokens = Object.values(player.tokens).reduce((a, b) => a + b, 0);
    const needToDiscard = totalTokens - 10;
    if (needToDiscard <= 0) return;

    const modalHtml = `
      <div style="text-align: center; padding: 1rem 0;">
        <h3 style="color: var(--color-danger); margin-bottom: 0.5rem;">⚠️ Trả Bớt Token Dư Thừa</h3>
        <p style="color: var(--color-cream-soft); margin-bottom: 1.25rem;">
          Bạn đang có <strong>${totalTokens} token</strong> (vượt quá giới hạn 10). Bạn cần chọn trả lại ít nhất <strong>${needToDiscard} token</strong> về kho chung.
        </p>

        <div id="discard-picker-list" style="display: flex; flex-direction: column; gap: 0.5rem; max-width: 320px; margin: 0 auto 1.5rem;">
          ${Object.entries(player.tokens).filter(([_, qty]) => qty > 0).map(([g, qty]) => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.4rem 0.8rem; background: rgba(37, 22, 32, 0.7); border-radius: var(--radius-sm);">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div class="gem-token gem-${g}" style="width:26px; height:26px; font-size: 0.7rem;"></div>
                <span style="font-weight: 700; text-transform: uppercase;">${g} (${qty})</span>
              </div>
              <input type="number" class="discard-qty-input form-input" data-gem="${g}" min="0" max="${qty}" value="0" style="width: 70px; padding: 0.3rem 0.5rem; text-align: center;">
            </div>
          `).join('')}
        </div>

        <button class="btn btn-danger btn-lg" id="btn-confirm-discard">
          Xác Nhận Trả Token
        </button>
      </div>
    `;

    Modal.open('Giới Hạn 10 Token', modalHtml);

    document.getElementById('btn-confirm-discard')?.addEventListener('click', () => {
      const inputs = document.querySelectorAll('.discard-qty-input');
      const discardData = {};
      let totalSelected = 0;

      inputs.forEach(inp => {
        const val = parseInt(inp.value, 10) || 0;
        if (val > 0) {
          discardData[inp.dataset.gem] = val;
          totalSelected += val;
        }
      });

      if (totalTokens - totalSelected > 10) {
        Toast.error(`Cần trả thêm ít nhất ${totalTokens - totalSelected - 10} token nữa`);
        return;
      }

      Modal.close();
      this.sendAction({
        type: 'discard_tokens',
        tokens: discardData
      });
    });
  }

  static async sendAction(action) {
    if (!this.isMyTurn() && this.gameState?.pending_discard_player === null) {
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
      } catch (e) {
        console.error(e);
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
        } else {
          Toast.error(res.error || 'Chỉ chủ phòng mới có thể bắt đầu lại');
        }
      } catch (e) {
        console.error(e);
        Toast.error('Không thể chơi lại');
      }
    } else {
      if (ApiService.socket && ApiService.socket.connected) {
        ApiService.requestRematchSocket(this.roomCode, AppState.participantToken);
      } else {
        await ApiService.requestRematchRest(this.roomCode, AppState.participantToken);
      }
      Toast.info('Đã gửi yêu cầu tái đấu. Chờ đối thủ đồng ý...');
      const btn = document.getElementById('btn-gk-restart');
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
        <div class="victory-icon">💎</div>
        <div class="victory-title">Bậc Thầy Đá Quý!</div>
        <div class="victory-detail">
          Chúc mừng <strong>${winner?.name || 'Người chơi'}</strong> đã đạt <strong>${winner?.prestige_points || 15} điểm Uy Tín</strong> (${winner?.cards_count || 0} thẻ) và giành chiến thắng chung cuộc!
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
      Router.navigate('local_setup', { game: 'gem_kingdom' });
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
}
