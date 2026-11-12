import { AppState } from '../state.js';
import { Router } from '../router.js';
import { Toast } from '../components/toast.js';
import { ApiService } from '../api.js';

export class LocalSetupView {
  static playerCount = 2;

  static render(container, params = {}) {
    const gameId = params.game || AppState.selectedGame || 'caro';
    const canSelectPlayers = (gameId !== 'caro');
    if (gameId === 'undercover') {
      this.playerCount = Math.max(3, Math.min(20, this.playerCount || 6));
    } else {
      this.playerCount = canSelectPlayers ? Math.max(2, Math.min(4, this.playerCount)) : 2;
    }

    const gameTitles = {
      'caro': 'Cờ Caro (Gomoku Freestyle) - 2 Người',
      'gem_kingdom': 'Gem Kingdom (Splendor) - 2 đến 4 Người',
      'ludo': 'Cờ Cá Ngựa (Ludo) - 2 đến 4 Người',
      'monopoly': 'Cờ Tỷ Phú (Property Tycoon) - 2 đến 4 Người',
      'undercover': 'Undercover (Ai Là Gián Điệp?) - 3 đến 20 Người'
    };

    const gameTitle = gameTitles[gameId] || 'Cờ Caro (2 Người)';

    let playerSelectorHtml = '';
    if (gameId === 'undercover') {
      const counts = [3, 4, 6, 8, 10, 12, 16, 20];
      playerSelectorHtml = `
        <div class="form-group">
          <label>Số lượng người chơi chính thức (3 - 20 người):</label>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
            ${counts.map(c => `
              <button class="btn btn-sm ${this.playerCount === c ? 'btn-primary' : 'btn-secondary'}" data-count="${c}">
                ${c} Người ${c === 6 ? '⭐' : ''}
              </button>
            `).join('')}
          </div>
        </div>
      `;
    } else if (canSelectPlayers) {
      playerSelectorHtml = `
        <div class="form-group">
          <label>Số lượng người chơi:</label>
          <div style="display: flex; gap: 0.75rem; margin-bottom: 1rem;">
            <button class="btn btn-sm ${this.playerCount === 2 ? 'btn-primary' : 'btn-secondary'}" data-count="2">2 Người</button>
            <button class="btn btn-sm ${this.playerCount === 3 ? 'btn-primary' : 'btn-secondary'}" data-count="3">3 Người</button>
            <button class="btn btn-sm ${this.playerCount === 4 ? 'btn-primary' : 'btn-secondary'}" data-count="4">4 Người</button>
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="lobby-container">
        <div class="lobby-header">
          <button class="btn btn-ghost btn-sm" id="btn-back-select" style="margin-bottom: 1rem;">
            ← Quay Lại Chọn Chế Độ
          </button>
          <h2>Cài Đặt Chơi Chung (Local 1 Máy)</h2>
          <p>Nhập tên người chơi để chuẩn bị bước vào ván đấu trên cùng một màn hình</p>
        </div>

        <div class="glass-panel setup-form-panel">
          <div class="form-group">
            <label>Trò chơi đã chọn:</label>
            <div style="font-weight: 700; color: var(--color-sunset-orange); font-size: 1.1rem; margin-bottom: 1rem;">
              ${gameTitle}
            </div>
          </div>

          ${playerSelectorHtml}

          <div id="players-input-list">
            ${this.renderPlayerInputs(this.playerCount, gameId)}
          </div>

          <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: flex-end;">
            <button class="btn btn-secondary" id="btn-cancel-setup">Hủy</button>
            <button class="btn btn-primary btn-lg" id="btn-start-local-game">
              <span>🚀</span> Bắt Đầu Ván Chơi
            </button>
          </div>
        </div>
      </div>
    `;

    this.attachEvents(container, gameId, canSelectPlayers);
  }

  static renderPlayerInputs(count, gameId) {
    const defaultSymbols = {
      'caro': ['X', 'O', '▲', '■'],
      'ludo': ['🐎1', '🐎2', '🐎3', '🐎4'],
      'monopoly': ['🚗', '🚢', '🎩', '🐎'],
      'gem_kingdom': ['P1', 'P2', 'P3', 'P4']
    };

    const symbols = defaultSymbols[gameId] || ['P1', 'P2', 'P3', 'P4'];

    const colors = [
      { color: '#FF9966', name: 'Sunset Orange' },
      { color: '#FFE1BA', name: 'Cream' },
      { color: '#BE807D', name: 'Dusty Rose' },
      { color: '#795463', name: 'Mauve' }
    ];

    let html = '';
    for (let i = 0; i < count; i++) {
      const c = colors[i % colors.length];
      const sym = symbols[i % symbols.length];
      html += `
        <div class="player-config-row">
          <div class="player-color-preview" style="background: ${c.color}; color: #251620;">
            ${sym}
          </div>
          <div style="flex: 1;">
            <label style="font-size: 0.8rem; color: var(--color-dusty-rose); display: block; margin-bottom: 0.25rem;">
              Người chơi ${i + 1} ${i === 0 ? '(Đi trước)' : ''}
            </label>
            <input type="text" id="p${i + 1}-name-input" class="form-input" value="Người chơi ${i + 1}" maxlength="20">
          </div>
        </div>
      `;
    }
    return html;
  }

  static attachEvents(container, gameId, canSelectPlayers) {
    document.getElementById('btn-back-select')?.addEventListener('click', () => {
      Router.navigate('game_select', { game: gameId });
    });

    document.getElementById('btn-cancel-setup')?.addEventListener('click', () => {
      Router.navigate('game_select', { game: gameId });
    });

    if (canSelectPlayers) {
      container.querySelectorAll('button[data-count]').forEach(btn => {
        btn.addEventListener('click', () => {
          this.playerCount = parseInt(btn.dataset.count, 10);
          this.render(container, { game: gameId });
        });
      });
    }

    document.getElementById('btn-start-local-game')?.addEventListener('click', async () => {
      const defaultSymbols = {
        'caro': ['X', 'O', '▲', '■'],
        'ludo': ['H1', 'H2', 'H3', 'H4'],
        'monopoly': ['🚗', '🚢', '🎩', '🐎'],
        'gem_kingdom': ['P1', 'P2', 'P3', 'P4']
      };

      const symbols = defaultSymbols[gameId] || ['P1', 'P2', 'P3', 'P4'];
      const colors = ['#FF9966', '#FFE1BA', '#BE807D', '#795463'];

      const localPlayers = [];
      for (let i = 0; i < this.playerCount; i++) {
        const inp = document.getElementById(`p${i + 1}-name-input`);
        const name = inp?.value.trim() || `Người chơi ${i + 1}`;
        localPlayers.push({
          name: name,
          color: colors[i % colors.length],
          symbol: symbols[i % symbols.length]
        });
      }

      try {
        const res = await ApiService.createRoom(gameId, localPlayers[0].name, true, localPlayers);
        if (res.success) {
          AppState.setSession(res.room_code, res.participant_token, 0, true, true);
          AppState.setRoom(res.room);
          Toast.success(`Đã khởi tạo ván đấu thành công!`);

          const targetView = (gameId === 'gem_kingdom') ? 'gem_kingdom_play'
            : (gameId === 'ludo') ? 'ludo_play'
            : (gameId === 'monopoly') ? 'monopoly_play'
            : (gameId === 'undercover') ? 'undercover_play'
            : 'caro_play';

          Router.navigate(targetView, { roomCode: res.room_code });
        } else {
          Toast.error(res.error || 'Không thể tạo ván đấu');
        }
      } catch (e) {
        console.error(e);
        Toast.error('Lỗi kết nối máy chủ');
      }
    });
  }
}
