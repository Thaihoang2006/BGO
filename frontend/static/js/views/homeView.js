import { AppState } from '../state.js';
import { Router } from '../router.js';
import { Toast } from '../components/toast.js';
import { ApiService } from '../api.js';

export class HomeView {
  static render(container) {
    container.innerHTML = `
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-badge">
          <span>✨</span> Nền tảng Board Game trực tuyến thế hệ mới
        </div>
        <h1 class="hero-title">
          Play Together, <span class="gradient-text">Anywhere.</span>
        </h1>
        <p class="hero-subtitle">
          Trải nghiệm board game ấm áp, kết nối bạn bè ngay trên trình duyệt. Hỗ trợ chơi chung 1 máy (Local) hoặc tạo phòng chơi từ xa (Online Multiplayer) với luật chơi chặt chẽ, mượt mà.
        </p>

        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" id="hero-btn-play">
            <span>🎲</span> Chơi Ngay (Chọn Game)
          </button>
          <button class="btn btn-sunset btn-lg" id="hero-btn-create-room">
            <span>➕</span> Tạo Phòng Online
          </button>
          <button class="btn btn-secondary btn-lg" id="hero-btn-rules">
            <span>📖</span> Hướng Dẫn Luật Chơi
          </button>
        </div>

        <!-- Quick Join Room Input -->
        <div class="glass-card quick-join-card">
          <input type="text" id="quick-join-input" class="quick-join-input" placeholder="Nhập mã phòng (vd: BGO742)" maxlength="8">
          <button class="btn btn-primary" id="quick-join-btn">
            <span>⚡</span> Vào Phòng Online
          </button>
        </div>
      </section>

      <!-- Games Showcase Section -->
      <section class="games-section">
        <div class="section-header">
          <div class="section-title">
            <h2>Bộ Sưu Tập Board Game</h2>
            <p>Chọn trò chơi yêu thích để bắt đầu ván đấu kịch tính cùng bạn bè</p>
          </div>
        </div>

        <div class="games-grid" id="games-grid-container">
          <!-- Game cards will be rendered here -->
        </div>
      </section>

      <!-- Features Pillars -->
      <section class="features-section">
        <div class="glass-card feature-item">
          <div class="feature-icon">💻</div>
          <h4>Local Multiplayer</h4>
          <p>Chơi chung trên 1 laptop/máy tính bằng cách chuyền tay thay phiên thao tác, không cần tạo tài khoản.</p>
        </div>
        <div class="glass-card feature-item">
          <div class="feature-icon">🌐</div>
          <h4>Online Multiplayer</h4>
          <p>Tạo phòng riêng, chia sẻ mã phòng ngắn gọn để bạn bè tham gia trên điện thoại hoặc máy tính khác.</p>
        </div>
        <div class="glass-card feature-item">
          <div class="feature-icon">🛡️</div>
          <h4>Server-Authoritative</h4>
          <p>Mọi nước đi, tung xúc xắc và tính điểm được backend xác thực tuyệt đối, chống gian lận và sai lệch.</p>
        </div>
        <div class="glass-card feature-item">
          <div class="feature-icon">🌅</div>
          <h4>Sunset Aesthetic</h4>
          <p>Giao diện ấm cúng, thư giãn lấy cảm hứng từ hoàng hôn, hiệu ứng glassmorphism mượt mà trên mọi thiết bị.</p>
        </div>
      </section>
    `;

    this.renderGameCards();
    this.attachEvents();
  }

  static renderGameCards() {
    const grid = document.getElementById('games-grid-container');
    if (!grid) return;

    const gamesData = [
      {
        id: 'caro',
        name: 'Cờ Caro (Gomoku)',
        subtitle: 'Trận chiến 5 quân liên tiếp',
        desc: 'Đấu trí đỉnh cao trên bàn cờ 15x15 phong cách hoàng hôn. Người đầu tiên xếp đủ 5 quân theo hàng ngang, dọc hoặc chéo sẽ chiến thắng.',
        icon: '⚔️',
        players: '2 người chơi',
        board: 'Bàn cờ 15x15',
        badge: 'Sẵn sàng',
        badgeClass: 'badge-ready',
        isReady: true
      },
      {
        id: 'ludo',
        name: 'Cờ Cá Ngựa (Ludo)',
        subtitle: 'Đua tài xúc xắc về đích',
        desc: 'Cuộc đua kịch tính của 4 đàn ngựa rực rỡ sắc màu. Tung nút 6 xuất chuồng, đá quân đối thủ, leo các bậc về đích an toàn.',
        icon: '🐴',
        players: '2 - 4 người chơi',
        board: 'Bàn cờ vuông 56 ô & 4 chuồng',
        badge: 'Sẵn sàng',
        badgeClass: 'badge-ready',
        isReady: true
      },
      {
        id: 'gem_kingdom',
        name: 'Gem Kingdom (Splendor)',
        subtitle: 'Thu thập đá quý & phát triển thẻ bài',
        desc: 'Đầy đủ luật chuẩn Splendor: 35 token 5 loại, 5 token Vàng (Wild), 90 thẻ 3 cấp, 10 thẻ Quý tộc, giới hạn 10 token, mốc 15 điểm chung kết.',
        icon: '💎',
        players: '2 - 4 người chơi',
        board: 'Bàn cờ 12 thẻ & Quý tộc',
        badge: 'Sẵn sàng',
        badgeClass: 'badge-ready',
        isReady: true
      },
      {
        id: 'monopoly',
        name: 'Cờ Tỷ Phú (Property Tycoon)',
        subtitle: 'Kinh doanh bất động sản & xây cơ đồ',
        desc: 'Gieo 2 xúc xắc, mua đất phố thị, xây nhà tăng tiền thuê, tránh vào tù, nhận thưởng qua vạch xuất phát và làm giàu.',
        icon: '🎩',
        players: '2 - 4 người chơi',
        board: 'Bàn cờ 24 ô phố',
        badge: 'Sẵn sàng',
        badgeClass: 'badge-ready',
        isReady: true
      },
      {
        id: 'undercover',
        name: 'Undercover (Ai Là Gián Điệp?)',
        subtitle: 'Trò chơi suy luận & tìm kẻ phản bội',
        desc: 'Đấu trí suy luận từ khóa bí mật: Dân Thường, Mũ Đen và Mr. White. Mô tả khéo léo, tranh luận sôi nổi, bỏ phiếu loại gián điệp. Hỗ trợ đến 20 người chơi & 30 khán giả theo dõi!',
        icon: '🕵️',
        players: '3 - 20 người chơi',
        board: 'Bàn suy luận & Bỏ phiếu kín',
        badge: 'Mới ra mắt 🔥',
        badgeClass: 'badge-ready',
        isReady: true
      }
    ];

    grid.innerHTML = gamesData.map(game => `
      <div class="glass-card game-card ${game.isReady ? 'active-ready' : ''}">
        <span class="game-card-badge ${game.badgeClass}">${game.badge}</span>
        <div>
          <div class="game-card-icon">${game.icon}</div>
          <div class="game-card-content">
            <h3>${game.name}</h3>
            <div class="game-card-subtitle">${game.subtitle}</div>
            <p class="game-card-desc">${game.desc}</p>
          </div>
        </div>

        <div>
          <div class="game-card-meta">
            <div class="meta-item"><span>👥</span> ${game.players}</div>
            <div class="meta-item"><span>📐</span> ${game.board}</div>
          </div>
          <div class="game-card-actions">
            ${game.isReady
              ? `<button class="btn btn-primary" data-action="play" data-game="${game.id}">Chơi Ngay</button>`
              : `<button class="btn btn-secondary" data-action="rules" data-game="${game.id}">Xem Luật</button>`
            }
            <button class="btn btn-ghost" data-action="rules" data-game="${game.id}">Luật Chơi</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  static attachEvents() {
    document.getElementById('hero-btn-play')?.addEventListener('click', () => {
      Router.navigate('game_select', { game: 'caro' });
    });

    document.getElementById('hero-btn-create-room')?.addEventListener('click', () => {
      Router.navigate('online_lobby', { game: 'caro', mode: 'create' });
    });

    document.getElementById('hero-btn-rules')?.addEventListener('click', () => {
      Router.navigate('rules', { game: 'caro' });
    });

    const joinBtn = document.getElementById('quick-join-btn');
    const joinInput = document.getElementById('quick-join-input');

    const handleJoin = async () => {
      const code = joinInput.value.trim().toUpperCase();
      if (!code) {
        Toast.error('Vui lòng nhập mã phòng');
        joinInput.focus();
        return;
      }
      Router.navigate('online_lobby', { roomCode: code, mode: 'join' });
    };

    joinBtn?.addEventListener('click', handleJoin);
    joinInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleJoin();
    });

    document.getElementById('games-grid-container')?.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-action]');
      if (!btn) return;
      const action = btn.dataset.action;
      const gameId = btn.dataset.game;

      if (action === 'play') {
        Router.navigate('game_select', { game: gameId });
      } else if (action === 'rules') {
        Router.navigate('rules', { game: gameId });
      }
    });
  }
}
