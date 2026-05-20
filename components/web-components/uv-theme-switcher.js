import UVElement from '/js/core/web-components-factory.js';
import ComponentRegistry from '/js/core/component-registry.js';
import '/js/features/design-tokens.js';

const template = `
  <label class="label" for="themeSelect">Theme</label>
  <select id="themeSelect" class="select" aria-label="Theme selector">
    <option value="system">System</option>
    <option value="light">Light</option>
    <option value="dark">Dark</option>
    <option value="ocean">Ocean</option>
    <option value="forest">Forest</option>
  </select>
  <p class="hint">Stored in localStorage and applied to the document root.</p>
`;

const styles = `
  :host {
    display: inline-flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 220px;
    font-family: var(--font-body, Arial, sans-serif);
  }

  .label {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-primary, #111111);
  }

  .select {
    padding: 0.7rem 0.85rem;
    border-radius: var(--radius-md, 14px);
    border: 1px solid var(--border-primary, #ebebeb);
    background: var(--bg-secondary, #ffffff);
    color: var(--text-primary, #111111);
    box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.06));
  }

  .hint {
    margin: 0;
    font-size: 0.78rem;
    color: var(--text-secondary, #666666);
  }
`;

class UVThemeSwitcher extends UVElement {
  constructor() {
    super({ useShadow: true, template, styles });
  }

  init() {
    this.select = this._root.querySelector('#themeSelect');
    const manager = window.DesignTokens;
    const current = localStorage.getItem(manager.STORAGE_KEY) || 'system';
    this.select.value = current;

    this.select.addEventListener('change', (event) => {
      manager.applyTheme(event.target.value);
      this.dispatchEvent(new CustomEvent('theme-change', {
        bubbles: true,
        composed: true,
        detail: {
          theme: event.target.value,
          resolvedTheme: manager.getResolvedTheme(event.target.value)
        }
      }));
    });

    window.addEventListener('design-tokens:themechange', (event) => {
      const next = event.detail?.theme || 'system';
      if (this.select && this.select.value !== next) {
        this.select.value = next;
      }
    });
  }
}

ComponentRegistry.define('uv-theme-switcher', UVThemeSwitcher);

if (!window.UV) window.UV = {};
window.UV.UVThemeSwitcher = UVThemeSwitcher;

export default UVThemeSwitcher;
