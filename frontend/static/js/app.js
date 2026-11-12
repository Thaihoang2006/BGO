import { ApiService } from './api.js';
import { Router } from './router.js';
import { AppState } from './state.js';
import { Toast } from './components/toast.js';
import { RoomChat } from './components/roomChat.js';

const initApp = async () => {
  console.log('🌅 Initializing BGO - Board Games Online...');

  // Initialize UI components
  Toast.init();
  ApiService.initSocket();
  RoomChat.init();

  // Synchronize RoomChat with room state
  AppState.subscribe((state) => {
    if (state.roomCode && !state.isLocal) {
      RoomChat.setRoom(state.roomCode, state.participantToken, false);
    } else {
      RoomChat.setRoom(null, null, true);
    }
  });

  // Initialize Theme Switcher (Sunset vs Citrus Mint)
  const applyTheme = (theme) => {
    const iconEl = document.getElementById('theme-icon');
    const textEl = document.getElementById('theme-text');
    if (theme === 'citrus-mint') {
      document.documentElement.setAttribute('data-theme', 'citrus-mint');
      if (iconEl) iconEl.textContent = '🍋';
      if (textEl) textEl.textContent = 'Citrus';
    } else {
      document.documentElement.removeAttribute('data-theme');
      if (iconEl) iconEl.textContent = '🌅';
      if (textEl) textEl.textContent = 'Sunset';
    }
  };

  const savedTheme = localStorage.getItem('bgo_theme') || 'sunset';
  applyTheme(savedTheme);

  document.getElementById('btn-toggle-theme')?.addEventListener('click', () => {
    const current = localStorage.getItem('bgo_theme') || 'sunset';
    const nextTheme = current === 'sunset' ? 'citrus-mint' : 'sunset';
    localStorage.setItem('bgo_theme', nextTheme);
    applyTheme(nextTheme);
    Toast.info(`Đã đổi giao diện sang: ${nextTheme === 'citrus-mint' ? '🍋 Citrus Mint (Mùa hè tươi mát)' : '🌅 Sunset (Hoàng hôn ấm áp)'}`);
  });

  // Attach Global Navigation Events
  document.getElementById('brand-logo-btn')?.addEventListener('click', () => {
    Router.navigate('home');
  });

  document.querySelectorAll('.nav-link-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const view = btn.dataset.view;
      if (view) {
        Router.navigate(view);
      }
    });
  });

  document.getElementById('current-room-pill')?.addEventListener('click', () => {
    if (AppState.roomCode) {
      navigator.clipboard.writeText(AppState.roomCode);
      Toast.success(`Đã sao chép mã phòng: ${AppState.roomCode}`);
      if (AppState.currentRoom?.status === 'playing') {
        const gt = AppState.currentRoom.game_type;
        let view = 'caro_play';
        if (gt === 'gem_kingdom') view = 'gem_kingdom_play';
        else if (gt === 'ludo') view = 'ludo_play';
        else if (gt === 'monopoly') view = 'monopoly_play';
        Router.navigate(view, { roomCode: AppState.roomCode });
      } else {
        Router.navigate('online_lobby', { roomCode: AppState.roomCode });
      }
    }
  });

  // Check and restore active room session if any
  const savedCode = sessionStorage.getItem('bgo_room_code');
  const savedToken = sessionStorage.getItem('bgo_token');
  if (savedCode && savedToken) {
    try {
      const data = await ApiService.getRoom(savedCode, savedToken);
      if (data.room) {
        AppState.setRoom(data.room);
        AppState.setSession(
          savedCode,
          savedToken,
          data.room.viewer_player_index,
          data.room.is_viewer_host,
          data.room.is_local
        );
      }
    } catch (e) {
      console.warn('Could not restore previous room session:', e);
    }
  }

  // Listen to global room events: player leave, disconnect, host transfer
  ApiService.on('player_left', (data) => {
    if (data.room_closed) {
      alert(data.message || 'Chủ phòng đã rời phòng. Trận đấu kết thúc và phòng đã giải tán!');
      AppState.clearSession();
      Router.navigate('home');
    } else {
      Toast.warning(data.message || `⚠️ Người chơi ${data.player_name} đã rời phòng.`);
    }
  });

  ApiService.on('player_disconnected', (data) => {
    Toast.warning(data.message || `⚠️ Người chơi ${data.name} đã mất kết nối!`);
  });

  ApiService.on('host_transferred', (data) => {
    Toast.info(`👑 ${data.old_host_name} đã chuyển quyền Chủ phòng cho ${data.new_host_name}!`);
    if (data.room) {
      AppState.setRoom(data.room);
    }
  });

  // Start Router
  console.log('👉 CALLING Router.init(app-root)...');
  Router.init('app-root');
  console.log('✅ Router.init finished!');
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
