import { AppState } from '../state.js';
import { Router } from '../router.js';

export class GameSelectView {
  static render(container, params = {}) {
    const gameId = params.game || AppState.selectedGame || 'caro';
    AppState.selectedGame = gameId;

    const gameNames = {
      caro: 'Cờ Caro (Gomoku)',
      ludo: 'Cờ Cá Ngựa (Ludo)',
      gem_kingdom: 'Gem Kingdom (Splendor)',
      monopoly: 'Cờ Tỷ Phú (Property Tycoon)',
      property_tycoon: 'Cờ Tỷ Phú (Property Tycoon)',
      undercover: 'Undercover – Ai Là Gián Điệp?'
    };

    container.innerHTML = `
      <div class="lobby-container">
        <div class="lobby-header">
          <button class="btn btn-ghost btn-sm" id="btn-back-home" style="margin-bottom: 1rem;">
            ← Quay Lại Trang Chủ
          </button>
          <h2>Chọn Chế Độ Chơi: ${gameNames[gameId] || 'Board Game'}</h2>
          <p>Bạn muốn chơi chung trên cùng một máy hay chơi trực tuyến giữa các thiết bị khác nhau?</p>
        </div>

        <div class="mode-selection-grid">
          <!-- Mode 1: Local Multiplayer -->
          <div class="glass-panel mode-card" id="card-mode-local">
            <div class="mode-icon">💻</div>
            <h3>Local Multiplayer</h3>
            <p>Nhiều người cùng ngồi quanh một máy tính/laptop, thay phiên nhau thao tác trên cùng một màn hình. Không cần kết nối mạng hay đăng nhập.</p>
            <div style="margin-top: 1.5rem;">
              <button class="btn btn-sunset" style="width: 100%;">
                Thiết Lập Chơi Chung (1 Máy)
              </button>
            </div>
          </div>

          <!-- Mode 2: Online Multiplayer -->
          <div class="glass-panel mode-card" id="card-mode-online">
            <div class="mode-icon">🌐</div>
            <h3>Online Multiplayer</h3>
            <p>Tạo phòng riêng và chia sẻ mã phòng ngắn (vd: BGO742) cho bạn bè trên điện thoại hoặc máy tính khác để cùng chơi thời gian thực.</p>
            <div style="margin-top: 1.5rem;">
              <button class="btn btn-primary" style="width: 100%;">
                Tạo Phòng / Vào Phòng Online
              </button>
            </div>
          </div>
        </div>

        <div style="text-align: center;">
          <button class="btn btn-ghost" id="btn-view-rules">
            📖 Xem lại luật chơi ${gameNames[gameId]}
          </button>
        </div>
      </div>
    `;

    this.attachEvents(gameId);
  }

  static attachEvents(gameId) {
    document.getElementById('btn-back-home')?.addEventListener('click', () => {
      Router.navigate('home');
    });

    document.getElementById('btn-view-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: gameId });
    });

    document.getElementById('card-mode-local')?.addEventListener('click', () => {
      Router.navigate('local_setup', { game: gameId });
    });

    document.getElementById('card-mode-online')?.addEventListener('click', () => {
      Router.navigate('online_lobby', { game: gameId, mode: 'create' });
    });
  }
}
