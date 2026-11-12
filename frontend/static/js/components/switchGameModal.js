import { Modal } from './modal.js';
import { ApiService } from '../api.js';
import { AppState } from '../state.js';
import { Toast } from './toast.js';
import { Router } from '../router.js';

export class SwitchGameModal {
  static open(roomCode, participantToken) {
    const games = [
      {
        id: 'caro',
        title: 'Cờ Caro (Gomoku)',
        icon: '⭕',
        desc: 'Bàn cờ mở rộng vô hạn. Đấu trí 5 quân liên tiếp.'
      },
      {
        id: 'ludo',
        title: 'Cờ Cá Ngựa (Ludo)',
        icon: '🐎',
        desc: 'Xúc xắc, đua 4 chú ngựa ra trận, đá ngựa đối thủ, về chuồng đích!'
      },
      {
        id: 'gem_kingdom',
        title: 'Gem Kingdom (Splendor)',
        icon: '💎',
        desc: 'Thu thập ngọc quý, mua thẻ tinh luyện, đón tiếp các Quý Tộc.'
      },
      {
        id: 'monopoly',
        title: 'Cờ Tỷ Phú (Property Tycoon)',
        icon: '🎩',
        desc: 'Mua đất, xây nhà, thu tiền thuê, tránh vào tù và làm giàu.'
      },
      {
        id: 'undercover',
        title: 'Undercover (Ai Là Gián Điệp?)',
        icon: '🕵️',
        desc: 'Trò chơi suy luận & tìm kẻ phản bội (3-20 người, có Khán Giả theo dõi).'
      }
    ];

    const currentType = AppState.currentRoom?.game_type || '';

    const html = `
      <div style="padding: 0.5rem 0;">
        <p style="color: var(--color-dusty-rose); margin-bottom: 1.25rem; font-size: 0.95rem;">
          Chủ phòng chọn trò chơi mới để chuyển cả phòng sang trò khác mà không cần tạo phòng lại:
        </p>

        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          ${games.map(g => `
            <div class="glass-panel" style="padding: 1rem; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: space-between; border: 1.5px solid ${g.id === currentType ? 'var(--color-sunset-orange)' : 'rgba(255,225,186,0.1)'}; background: ${g.id === currentType ? 'rgba(255,153,102,0.12)' : 'rgba(37,22,32,0.6)'};">
              <div style="display: flex; align-items: center; gap: 0.85rem;">
                <span style="font-size: 2rem;">${g.icon}</span>
                <div>
                  <h4 style="color: var(--color-cream); margin-bottom: 0.2rem; font-size: 1.05rem;">
                    ${g.title}
                    ${g.id === currentType ? '<span style="font-size: 0.75rem; color: var(--color-sunset-orange); margin-left: 0.5rem;">(Hiện tại)</span>' : ''}
                  </h4>
                  <p style="color: var(--color-cream-soft); font-size: 0.8rem; margin: 0;">${g.desc}</p>
                </div>
              </div>

              ${g.id === currentType ? `
                <span style="font-size: 0.85rem; color: var(--color-dusty-rose); font-weight: 700;">Đang chọn</span>
              ` : `
                <button class="btn btn-sunset btn-sm btn-select-new-game" data-game="${g.id}">
                  Đổi Sang
                </button>
              `}
            </div>
          `).join('')}
        </div>
      </div>
    `;

    Modal.open('🎮 Đổi Trò Chơi Trong Phòng', html);

    document.querySelectorAll('.btn-select-new-game').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const newGame = e.target.dataset.game;
        Modal.close();

        if (ApiService.socket && ApiService.socket.connected) {
          ApiService.switchGameSocket(roomCode, participantToken, newGame);
        } else {
          try {
            const res = await ApiService.switchGameRest(roomCode, participantToken, newGame);
            if (res.success) {
              Toast.success('Đã đổi trò chơi thành công!');
              AppState.setRoom(res.room);
              if (res.room.is_local) {
                Router.navigate('local_setup', { game: newGame });
              } else {
                Router.navigate('online_lobby', { roomCode: res.room.room_code, mode: 'lobby' });
              }
            } else {
              Toast.error(res.error || 'Không thể đổi trò chơi');
            }
          } catch (err) {
            Toast.error('Lỗi khi đổi trò chơi');
          }
        }
      });
    });
  }
}
