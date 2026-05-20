/**
 * Component Index
 * Scans and indexes all component files for search functionality
 */

const ComponentIndex = (function () {
  const _state = {
    initialized: false,
    components: [],
    fuse: null
  };

  /**
   * Extract component metadata from HTML file content
   */
  function extractMetadata(htmlContent, filename) {
    const metadata = {
      id: filename.replace('.html', ''),
      title: '',
      description: '',
      path: filename,
      category: 'Component',
      icon: 'fa-solid fa-circle',
      tags: []
    };

    // Extract title from <title> tag
    const titleMatch = htmlContent.match(/<title>([^<]+)<\/title>/i);
    if (titleMatch) {
      metadata.title = titleMatch[1].replace('— UIverse', '').trim();
    } else {
      metadata.title = filename.replace('.html', '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // Extract description from meta description if available
    const descMatch = htmlContent.match(/<meta name="description" content="([^"]+)"/i);
    if (descMatch) {
      metadata.description = descMatch[1];
    }

    // Extract category based on file naming patterns
    if (filename.includes('button') || filename.includes('btn')) {
      metadata.category = 'Buttons';
      metadata.icon = 'fa-solid fa-hand-pointer';
    } else if (filename.includes('navbar') || filename.includes('nav')) {
      metadata.category = 'Navigation';
      metadata.icon = 'fa-solid fa-bars';
    } else if (filename.includes('card')) {
      metadata.category = 'Cards';
      metadata.icon = 'fa-solid fa-table-cells-large';
    } else if (filename.includes('input') || filename.includes('form')) {
      metadata.category = 'Forms';
      metadata.icon = 'fa-solid fa-keyboard';
    } else if (filename.includes('badge')) {
      metadata.category = 'Badges';
      metadata.icon = 'fa-solid fa-award';
    } else if (filename.includes('alert')) {
      metadata.category = 'Alerts';
      metadata.icon = 'fa-solid fa-triangle-exclamation';
    } else if (filename.includes('loader') || filename.includes('spinner')) {
      metadata.category = 'Loaders';
      metadata.icon = 'fa-solid fa-spinner';
    } else if (filename.includes('modal') || filename.includes('popup')) {
      metadata.category = 'Modals';
      metadata.icon = 'fa-solid fa-window-maximize';
    } else if (filename.includes('dropdown') || filename.includes('menu')) {
      metadata.category = 'Navigation';
      metadata.icon = 'fa-solid fa-bars';
    } else if (filename.includes('table')) {
      metadata.category = 'Tables';
      metadata.icon = 'fa-solid fa-table';
    } else if (filename.includes('tab')) {
      metadata.category = 'Tabs';
      metadata.icon = 'fa-solid fa-table-columns';
    } else if (filename.includes('footer')) {
      metadata.category = 'Layout';
      metadata.icon = 'fa-solid fa-footer';
    } else if (filename.includes('header')) {
      metadata.category = 'Layout';
      metadata.icon = 'fa-solid fa-heading';
    } else if (filename.includes('color') || filename.includes('palette')) {
      metadata.category = 'Colors';
      metadata.icon = 'fa-solid fa-palette';
    } else if (filename.includes('icon')) {
      metadata.category = 'Icons';
      metadata.icon = 'fa-solid fa-icons';
    } else if (filename.includes('animation') || filename.includes('transition')) {
      metadata.category = 'Animations';
      metadata.icon = 'fa-solid fa-wand-magic-sparkles';
    } else if (filename.includes('chart') || filename.includes('graph')) {
      metadata.category = 'Charts';
      metadata.icon = 'fa-solid fa-chart-line';
    } else if (filename.includes('calendar') || filename.includes('date')) {
      metadata.category = 'Calendar';
      metadata.icon = 'fa-solid fa-calendar';
    } else if (filename.includes('map')) {
      metadata.category = 'Maps';
      metadata.icon = 'fa-solid fa-map-location-dot';
    } else if (filename.includes('pricing')) {
      metadata.category = 'Pricing';
      metadata.icon = 'fa-solid fa-tags';
    } else if (filename.includes('testimonial') || filename.includes('review')) {
      metadata.category = 'Testimonials';
      metadata.icon = 'fa-solid fa-comments';
    } else if (filename.includes('gallery') || filename.includes('image')) {
      metadata.category = 'Gallery';
      metadata.icon = 'fa-solid fa-images';
    } else if (filename.includes('blog') || filename.includes('article')) {
      metadata.category = 'Content';
      metadata.icon = 'fa-solid fa-newspaper';
    } else if (filename.includes('contact')) {
      metadata.category = 'Forms';
      metadata.icon = 'fa-solid fa-envelope';
    } else if (filename.includes('about') || filename.includes('faq') || filename.includes('documentation')) {
      metadata.category = 'Utility';
      metadata.icon = 'fa-solid fa-circle-info';
    }

    // Extract tags from content (look for common keywords)
    const keywords = ['responsive', 'dark', 'light', 'modern', 'minimal', 'gradient', 'glass', 'neon', 'animated', 'interactive', 'accessible'];
    const contentLower = htmlContent.toLowerCase();
    keywords.forEach(keyword => {
      if (contentLower.includes(keyword)) {
        metadata.tags.push(keyword);
      }
    });

    return metadata;
  }

  /**
   * Build component index from sidebar navigation
   */
  function buildFromSidebar() {
    const items = [];
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');

    sidebarLinks.forEach((link) => {
      const href = link.getAttribute('href');
      const iconEl = link.querySelector('i');
      const textEl = link.querySelector('span');

      if (href && textEl && href.endsWith('.html')) {
        items.push({
          id: href.replace('.html', ''),
          title: textEl.textContent.trim(),
          path: href,
          icon: iconEl ? iconEl.className : 'fa-solid fa-circle',
          category: 'Component',
          description: '',
          tags: []
        });
      }
    });

    return items;
  }

  /**
   * Initialize Fuse.js with component index
   */
  function initFuse() {
    if (typeof Fuse === 'undefined') {
      console.warn('[ComponentIndex] Fuse.js not loaded. Using fallback search.');
      return null;
    }

    const fuseOptions = {
      keys: [
        { name: 'title', weight: 0.7 },
        { name: 'category', weight: 0.2 },
        { name: 'tags', weight: 0.1 },
        { name: 'description', weight: 0.1 }
      ],
      threshold: 0.3,
      distance: 100,
      minMatchCharLength: 2,
      includeScore: true,
      ignoreLocation: true
    };

    return new Fuse(_state.components, fuseOptions);
  }

  /**
   * Search components using Fuse.js
   */
  function search(query) {
    if (!query || !query.trim()) {
      return _state.components.slice(0, 10);
    }

    if (_state.fuse) {
      const results = _state.fuse.search(query);
      return results.map(result => result.item);
    }

    // Fallback: simple filter if Fuse.js not available
    const queryLower = query.toLowerCase();
    return _state.components.filter(comp => 
      comp.title.toLowerCase().includes(queryLower) ||
      comp.category.toLowerCase().includes(queryLower) ||
      comp.tags.some(tag => tag.toLowerCase().includes(queryLower))
    ).slice(0, 10);
  }

  /**
   * Initialize component index
   */
  async function init() {
    if (_state.initialized) return;

    console.log('[ComponentIndex] Initializing...');

    // Build index from sidebar (client-side approach)
    _state.components = buildFromSidebar();
    console.log('[ComponentIndex] Found', _state.components.length, 'components from sidebar');

    // Initialize Fuse.js
    _state.fuse = initFuse();
    if (_state.fuse) {
      console.log('[ComponentIndex] Fuse.js initialized successfully');
    } else {
      console.warn('[ComponentIndex] Fuse.js not available, using fallback search');
    }

    _state.initialized = true;

    console.log('[ComponentIndex] Initialization complete');
  }

  /**
   * Get all components
   */
  function getAll() {
    return _state.components;
  }

  /**
   * Get component by ID
   */
  function getById(id) {
    return _state.components.find(comp => comp.id === id);
  }

  /**
   * Get components by category
   */
  function getByCategory(category) {
    return _state.components.filter(comp => 
      comp.category.toLowerCase() === category.toLowerCase()
    );
  }

  return {
    init,
    search,
    getAll,
    getById,
    getByCategory
  };
})();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ComponentIndex;
}
