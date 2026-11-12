import { Modal } from './modal.js';
import { ApiService } from '../api.js';
import { AppState } from '../state.js';
import { Router } from '../router.js';

export class LeaveRoomHelper {
  static promptLeave(roomCode, participantToken, isHost, isLocal) {
    if (isLocal) {
      if (confirm('Bạn có chắc muốn kết thúc ván đấu và quay về trang chủ?')) {
        AppState.clearSession();
        Router.navigate('home');
      }
      return;
    }

    const room = AppState.currentRoom;
    const players = (room?.players || []).filter(p => !p.is_you && p.participant_token !== participantToken && p.is_connected && !p.is_spectator);

    if (isHost && players.length > 0) {
      const optionsHtml = players.map(p => `<option value="${p.player_index}">${p.name} (Người chơi ${p.player_index + 1})</option>`).join('');

      const html = `
        <div style="padding: 0.5rem 0;">
          <p style="color: #FC8181; font-weight: 700; margin-bottom: 0.75rem;">
            ⚠️ Bạn đang là Chủ phòng!
          </p>
          <p style="color: var(--color-dusty-rose); font-size: 0.9rem; margin-bottom: 1.25rem;">
            Nếu bạn thoát mà không chuyển quyền, phòng sẽ bị <strong>giải tán hoàn toàn</strong> và tất cả người chơi khác đều bị đưa ra ngoài.
          </p>

          <div class="glass-panel" style="padding: 1rem; margin-bottom: 1.25rem; border: 1px solid var(--surface-glass-border); border-radius: var(--radius-md);">
            <label style="display: block; font-size: 0.85rem; color: var(--color-cream); font-weight: 700; margin-bottom: 0.5rem;">
              👑 Chọn người nhận quyền Chủ phòng:
            </label>
            <select id="select-new-host" class="form-input" style="width: 100%; padding: 0.6rem; margin-bottom: 0.75rem;">
              ${optionsHtml}
            </select>
            <button id="btn-transfer-and-leave" class="btn btn-sunset" style="width: 100%;">
              Chuyển Quyền & Rời Đi
            </button>
          </div>

          <div style="text-align: center;">
            <button id="btn-disband-and-leave" class="btn btn-danger" style="width: 100%;">
              ✕ Giải Tán Phòng (Mọi người đều thoát)
            </button>
          </div>
        </div>
      `;

      Modal.open('🚪 Rời Phòng Chơi', html);

      document.getElementById('btn-transfer-and-leave')?.addEventListener('click', () => {
        const select = document.getElementById('select-new-host');
        const newIdx = parseInt(select.value);
        Modal.close();
        ApiService.transferHostSocket(roomCode, participantToken, newIdx);
        setTimeout(() => {
          ApiService.leaveRoomSocket(roomCode, participantToken);
          AppState.clearSession();
          Router.navigate('home');
        }, 150);
      });

      document.getElementById('btn-disband-and-leave')?.addEventListener('click', () => {
        Modal.close();
        ApiService.leaveRoomSocket(roomCode, participantToken);
        AppState.clearSession();
        Router.navigate('home');
      });
      return;
    }

    const msg = isHost
      ? 'Bạn là chủ phòng. Bạn có chắc muốn giải tán phòng và về trang chủ?'
      : 'Bạn có chắc chắn muốn rời phòng?';
    if (confirm(msg)) {
      ApiService.leaveRoomSocket(roomCode, participantToken);
      AppState.clearSession();
      Router.navigate('home');
    }
  }
}
