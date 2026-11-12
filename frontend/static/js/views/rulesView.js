import { Router } from '../router.js';
import { ApiService } from '../api.js';

export class RulesView {
  static activeTab = 'caro';

  static async render(container, params = {}) {
    this.activeTab = params.game || this.activeTab || 'caro';

    container.innerHTML = `
      <div class="lobby-container">
        <div class="lobby-header">
          <button class="btn btn-ghost btn-sm" id="btn-rules-back" style="margin-bottom: 1rem;">
            ← Quay Lại
          </button>
          <h2>📖 Sổ Tay Luật Chơi BGO</h2>
          <p>Tìm hiểu chi tiết mục tiêu, cách đi quân và bí quyết chiến thắng cho từng trò chơi</p>
        </div>

        <!-- Game Selection Tabs -->
        <div class="rules-tabs">
          <button class="rules-tab-btn ${this.activeTab === 'caro' ? 'active' : ''}" data-tab="caro">⚔️ Cờ Caro</button>
          <button class="rules-tab-btn ${this.activeTab === 'ludo' ? 'active' : ''}" data-tab="ludo">🐴 Cờ Cá Ngựa</button>
          <button class="rules-tab-btn ${this.activeTab === 'gem_kingdom' ? 'active' : ''}" data-tab="gem_kingdom">💎 Gem Kingdom</button>
          <button class="rules-tab-btn ${this.activeTab === 'monopoly' ? 'active' : ''}" data-tab="monopoly">🏰 Cờ Tỷ Phú</button>
          <button class="rules-tab-btn ${this.activeTab === 'undercover' ? 'active' : ''}" data-tab="undercover">🕵️ Undercover</button>
        </div>

        <div class="glass-panel" id="rules-content-box" style="padding: 2rem;">
          <div style="text-align: center; color: var(--color-dusty-rose);">Đang tải luật chơi...</div>
        </div>
      </div>
    `;

    document.getElementById('btn-rules-back')?.addEventListener('click', () => {
      window.history.back();
    });

    const tabs = container.querySelectorAll('.rules-tab-btn');
    tabs.forEach(btn => {
      btn.addEventListener('click', () => {
        tabs.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeTab = btn.dataset.tab;
        this.loadAndDisplayRules(this.activeTab);
      });
    });

    await this.loadAndDisplayRules(this.activeTab);
  }

  static async loadAndDisplayRules(gameType) {
    const box = document.getElementById('rules-content-box');
    if (!box) return;

    try {
      const data = await ApiService.getRules(gameType);
      const r = data.rules;

      box.innerHTML = `
        <h3 style="font-size: 1.5rem; color: var(--color-cream); margin-bottom: 1.25rem;">
          ${r.title}
        </h3>

        <div class="rule-section-block">
          <div class="rule-section-title">🎯 Mục Tiêu Trò Chơi</div>
          <div class="rule-section-content">${r.objective}</div>
        </div>

        <div class="rule-section-block">
          <div class="rule-section-title">👥 Số Lượng Người Chơi & Chuẩn Bị</div>
          <div class="rule-section-content">
            <p><strong>Người chơi:</strong> ${r.players}</p>
            <ul class="rule-list">
              ${r.setup.map(item => `<li>${item}</li>`).join('')}
            </ul>
          </div>
        </div>

        <div class="rule-section-block">
          <div class="rule-section-title">🎲 Luật Theo Lượt & Cách Đi</div>
          <div class="rule-section-content">
            <ul class="rule-list">
              ${r.gameplay.map(item => `<li>${item}</li>`).join('')}
            </ul>
          </div>
        </div>

        <div class="rule-section-block">
          <div class="rule-section-title">🏆 Điều Kiện Thắng / Hòa</div>
          <div class="rule-section-content">
            <ul class="rule-list">
              ${r.win_conditions.map(item => `<li>${item}</li>`).join('')}
            </ul>
          </div>
        </div>

        ${r.tips && r.tips.length ? `
          <div class="rule-tips-box">
            <strong>💡 Mẹo cao thủ:</strong>
            <ul style="padding-left: 1.2rem; margin-top: 0.35rem;">
              ${r.tips.map(t => `<li>${t}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      `;
    } catch (e) {
      console.error(e);
      box.innerHTML = `<div style="color: var(--color-danger);">Không thể tải thông tin luật chơi. Vui lòng thử lại.</div>`;
    }
  }
}
