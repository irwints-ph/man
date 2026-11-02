let rawFilesList = [];
    let currentFile = null;
    let currentRaw = '';
    let collapsedFolders = new Set();
    let isSearchActive = false;

    // Document Font Size Zoom Controller
    let currentDocZoom = parseFloat(localStorage.getItem('mdp-doc-zoom') || '1.0');

    function applyDocZoom() {
      document.documentElement.style.setProperty('--doc-zoom', currentDocZoom);
      const label = document.getElementById('doc-zoom-label');
      if (label) label.textContent = `${Math.round(currentDocZoom * 100)}%`;
      localStorage.setItem('mdp-doc-zoom', currentDocZoom);
    }

    function adjustDocZoom(delta) {
      currentDocZoom = Math.min(Math.max(Math.round((currentDocZoom + delta) * 10) / 10, 0.7), 2.2);
      applyDocZoom();
    }

    function resetDocZoom() {
      currentDocZoom = 1.0;
      applyDocZoom();
    }

    // Initialize Theme & Zoom
    const savedTheme = localStorage.getItem('md-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(savedTheme);
    applyDocZoom();

    document.getElementById('btn-theme').addEventListener('click', () => {
      const nextTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      setTheme(nextTheme);
      // Re-render current file if it has mermaid diagrams so colors adapt
      if (currentFile) openFile(currentFile);
    });

    function setTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.setAttribute('data-color-mode', theme);
      document.documentElement.setAttribute('data-dark-theme', 'dark');
      document.documentElement.setAttribute('data-light-theme', 'light');
      localStorage.setItem('md-theme', theme);
      const hljsLight = document.getElementById('hljs-light');
      const hljsDark = document.getElementById('hljs-dark');
      if (hljsLight && hljsDark) {
        hljsLight.disabled = (theme === 'dark');
        hljsDark.disabled = (theme !== 'dark');
      }
    }

    // Reading Canvas Width Controller (Wide: 1450px, Full: 100%, Normal: 1100px)
    let currentWidthMode = localStorage.getItem('mdp-content-width') || 'wide';

    function applyWidthMode(mode) {
      currentWidthMode = mode;
      localStorage.setItem('mdp-content-width', mode);
      const btn = document.getElementById('btn-width');
      let val = '1450px';
      if (mode === 'full') {
        val = '100%';
        if (btn) btn.textContent = '⬛ Full';
      } else if (mode === 'normal') {
        val = '1100px';
        if (btn) btn.textContent = '🗖 Normal';
      } else {
        val = '1450px';
        if (btn) btn.textContent = '⛶ Wide';
      }
      document.documentElement.style.setProperty('--content-max-width', val);
    }

    applyWidthMode(currentWidthMode);

    const btnWidth = document.getElementById('btn-width');
    if (btnWidth) {
      btnWidth.addEventListener('click', () => {
        const nextMode = currentWidthMode === 'wide' ? 'full' : (currentWidthMode === 'full' ? 'normal' : 'wide');
        applyWidthMode(nextMode);
      });
    }

    // Toggle Sidebar (Desktop collapse & Mobile slide)
    const sidebar = document.getElementById('sidebar');
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    if (btnToggleSidebar) {
      btnToggleSidebar.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          sidebar.classList.toggle('open');
        } else {
          sidebar.classList.toggle('collapsed');
          const isCollapsed = sidebar.classList.contains('collapsed');
          btnToggleSidebar.classList.toggle('active', isCollapsed);
          localStorage.setItem('mdp-sidebar-collapsed', isCollapsed ? '1' : '0');
        }
      });
    }

    if (localStorage.getItem('mdp-sidebar-collapsed') === '1' && window.innerWidth > 768) {
      if (sidebar) sidebar.classList.add('collapsed');
      if (btnToggleSidebar) btnToggleSidebar.classList.add('active');
    }

    // Toggle TOC Drawer
    const tocDrawer = document.getElementById('toc-drawer');
    document.getElementById('btn-toc').addEventListener('click', () => {
      tocDrawer.classList.toggle('open');
    });

    // Keyboard Shortcuts (Ctrl+K for search, ESC for modal, Ctrl + / - for Zoom)
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === '=' || e.key === '+')) {
        e.preventDefault();
        adjustDocZoom(0.1);
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === '-' || e.key === '_')) {
        e.preventDefault();
        adjustDocZoom(-0.1);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault();
        resetDocZoom();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input').focus();
      }
      if (e.key === 'Escape') {
        closeLightbox();
        tocDrawer.classList.remove('open');
      }
    });
