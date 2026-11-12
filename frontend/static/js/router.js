import { AppState } from './state.js';
import { HomeView } from './views/homeView.js';
import { GameSelectView } from './views/gameSelectView.js';
import { LocalSetupView } from './views/localSetupView.js';
import { OnlineLobbyView } from './views/onlineLobbyView.js';
import { CaroGameView } from './views/games/caroGameView.js';
import { GemKingdomView } from './views/games/gemKingdomView.js';
import { LudoGameView } from './views/games/ludoGameView.js';
import { MonopolyGameView } from './views/games/monopolyGameView.js';
import { UndercoverGameView } from './views/games/undercoverGameView.js';
import { RulesView } from './views/rulesView.js';

export class Router {
  static container = null;
  static currentViewClass = null;

  static getView(viewName) {
    const map = {
      'home': HomeView,
      'game_select': GameSelectView,
      'local_setup': LocalSetupView,
      'online_lobby': OnlineLobbyView,
      'caro_play': CaroGameView,
      'gem_kingdom_play': GemKingdomView,
      'ludo_play': LudoGameView,
      'monopoly_play': MonopolyGameView,
      'undercover_play': UndercoverGameView,
      'rules': RulesView
    };
    return map[viewName] || HomeView;
  }

  static get viewMap() {
    return {
      'home': HomeView,
      'game_select': GameSelectView,
      'local_setup': LocalSetupView,
      'online_lobby': OnlineLobbyView,
      'caro_play': CaroGameView,
      'gem_kingdom_play': GemKingdomView,
      'ludo_play': LudoGameView,
      'monopoly_play': MonopolyGameView,
      'undercover_play': UndercoverGameView,
      'rules': RulesView
    };
  }

  static init(containerId = 'app-root') {
    console.log('👉 Router.init started, containerId:', containerId);
    this.container = document.getElementById(containerId);
    console.log('👉 Router.init container found:', !!this.container);

    window.addEventListener('hashchange', () => {
      this.handleHashChange();
    });

    this.handleHashChange();
    console.log('👉 Router.init completed handleHashChange!');
  }

  static navigate(viewName, params = {}) {
    AppState.currentView = viewName;

    // Build URL hash
    const query = new URLSearchParams(params).toString();
    const hash = query ? `#${viewName}?${query}` : `#${viewName}`;
    if (window.location.hash !== hash) {
      window.location.hash = hash;
    } else {
      this.renderView(viewName, params);
    }
  }

  static handleHashChange() {
    const rawHash = window.location.hash.slice(1) || 'home';
    console.log('👉 Router.handleHashChange rawHash:', rawHash);
    const [viewName, queryString] = rawHash.split('?');
    const params = {};
    if (queryString) {
      const searchParams = new URLSearchParams(queryString);
      for (const [key, val] of searchParams.entries()) {
        params[key] = val;
      }
    }

    this.renderView(viewName, params);
  }

  static renderView(viewName, params) {
    console.log('👉 Router.renderView called for:', viewName, 'container exists:', !!this.container);
    if (!this.container) return;

    this.updateActiveNav(viewName);

    // Clean up previous view if it had active listeners
    if (this.currentViewClass && typeof this.currentViewClass.cleanup === 'function') {
      try {
        this.currentViewClass.cleanup();
      } catch (err) {
        console.error('Error during view cleanup:', err);
      }
    }

    const TargetView = this.viewMap[viewName] || HomeView;
    console.log('👉 Router TargetView resolved:', TargetView ? TargetView.name : 'null');
    this.currentViewClass = TargetView;
    TargetView.render(this.container, params);
    console.log('👉 Router TargetView.render finished, container HTML len:', this.container.innerHTML.length);
  }

  static updateActiveNav(viewName) {
    document.querySelectorAll('.nav-link-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === viewName);
    });
  }
}
