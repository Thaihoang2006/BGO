export class Modal {
  static open(title, contentHtml, onCloseCallback = null) {
    let overlay = document.getElementById('global-modal-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'global-modal-overlay';
      overlay.className = 'modal-overlay';
      overlay.innerHTML = `
        <div class="modal-box">
          <div class="modal-header">
            <h3 class="modal-title" id="global-modal-title"></h3>
            <button class="modal-close-btn" id="global-modal-close">&times;</button>
          </div>
          <div class="modal-body" id="global-modal-body"></div>
        </div>
      `;
      document.body.appendChild(overlay);

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          Modal.close();
        }
      });

      document.getElementById('global-modal-close').addEventListener('click', () => {
        Modal.close();
      });
    }

    document.getElementById('global-modal-title').textContent = title;
    document.getElementById('global-modal-body').innerHTML = contentHtml;
    overlay.classList.add('active');
    Modal._onClose = onCloseCallback;
  }

  static close() {
    const overlay = document.getElementById('global-modal-overlay');
    if (overlay) {
      overlay.classList.remove('active');
      if (typeof Modal._onClose === 'function') {
        Modal._onClose();
        Modal._onClose = null;
      }
    }
  }
}
