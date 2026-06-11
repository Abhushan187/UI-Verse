class UVModal extends HTMLElement {
    constructor() {
        super();
        this._opened = false;
        const s = this.attachShadow({ mode: 'open' });
        s.innerHTML = `
      <style>
        :host {
          display: none;
        }
        :host([opened]) {
          display: block;
        }
      </style>
      <div><slot></slot></div>
    `;
    }
    get opened() {
        return this._opened;
    }
    set opened(val) {
        this._opened = val;
        if (val) {
            this.setAttribute('opened', '');
        }
        else {
            this.removeAttribute('opened');
        }
    }
    open() {
        this.opened = true;
    }
    close() {
        this.opened = false;
    }
}
if (typeof customElements !== 'undefined' && !customElements.get('uv-modal')) {
    customElements.define('uv-modal', UVModal);
}

export { UVModal };
//# sourceMappingURL=uv-modal.mjs.map
