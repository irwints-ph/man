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

    // Toggle Sidebar for mobile
    const sidebar = document.getElementById('sidebar');
    document.getElementById('btn-toggle-sidebar').addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

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
