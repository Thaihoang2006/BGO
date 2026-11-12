import { Modal } from './modal.js';
import { ApiService } from '../api.js';
import { Toast } from './toast.js';

export class RematchModal {
  static showInvitation(roomCode, participantToken, requesterName) {
    const html = `
      <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.75rem;">⚔️</div>
        <h3 style="color: var(--color-cream); margin-bottom: 0.5rem; font-size: 1.3rem;">Lời Mời Tái Đấu!</h3>
        <p style="color: var(--color-sunset-orange); font-size: 1.05rem; margin-bottom: 1.5rem;">
          <strong>${requesterName}</strong> muốn bắt đầu ván mới cùng bạn.
        </p>

        <div style="display: flex; gap: 1rem; justify-content: center;">
          <button class="btn btn-sunset btn-lg" id="btn-accept-rematch">
            ✓ Đồng Ý Tái Đấu
          </button>
          <button class="btn btn-secondary btn-lg" id="btn-decline-rematch">
            ✕ Từ Chối
          </button>
        </div>
      </div>
    `;

    Modal.open('Yêu Cầu Chơi Lại', html);

    document.getElementById('btn-accept-rematch')?.addEventListener('click', () => {
      Modal.close();
      if (ApiService.socket && ApiService.socket.connected) {
        ApiService.requestRematchSocket(roomCode, participantToken);
      } else {
        ApiService.requestRematchRest(roomCode, participantToken);
      }
    });

    document.getElementById('btn-decline-rematch')?.addEventListener('click', () => {
      Modal.close();
      if (ApiService.socket && ApiService.socket.connected) {
        ApiService.declineRematchSocket(roomCode, participantToken);
      } else {
        ApiService.declineRematchRest(roomCode, participantToken);
      }
    });
  }
}
