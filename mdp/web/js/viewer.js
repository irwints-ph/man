// Fetch and display Markdown File List
    async function loadFiles() {
      try {
        const res = await fetch('/api/files');
        const data = await res.json();
        rawFilesList = data.files || [];
        document.getElementById('root-dir-badge').textContent = data.root || '_docs';
        document.getElementById('file-count').textContent = rawFilesList.length + ' files';

        // Check if user requested expanding all folders via URL param ?expand=1 or CLI flag default_expand
        const urlParams = new URLSearchParams(window.location.search);
        const shouldExpand = urlParams.get('expand') === '1' || urlParams.get('expand') === 'true' || Boolean(data.default_expand);

        if (shouldExpand) {
          collapsedFolders.clear();
        } else {
          // Default: Collapse all folders
          collapsedFolders.clear();
          rawFilesList.forEach(f => {
            const parts = f.path.split('/');
            for (let i = 1; i < parts.length; i++) {
              collapsedFolders.add(parts.slice(0, i).join('/'));
            }
          });
        }

        // Auto-select first file or query param
        const fileParam = urlParams.get('file');
        let selectedFile = null;
        if (fileParam && rawFilesList.some(f => f.path === fileParam)) {
          selectedFile = fileParam;
        } else if (rawFilesList.length > 0) {
          // Prioritize Markdown files in the root folder first
          const rootFiles = rawFilesList.filter(f => !f.path.includes('/'));
          if (rootFiles.length > 0) {
            // Prioritize README.md / readme.md if present among root files
            const readme = rootFiles.find(f => f.name.toLowerCase() === 'readme.md');
            selectedFile = readme ? readme.path : rootFiles[0].path;
          } else {
            // If none in root folder, open the 1st document inside the folders
            selectedFile = rawFilesList[0].path;
          }
        }

        // Ensure parent folders of the active file are expanded so it is visible in the tree
        if (selectedFile) {
          const parts = selectedFile.split('/');
          for (let i = 1; i < parts.length; i++) {
            collapsedFolders.delete(parts.slice(0, i).join('/'));
          }
        }

        renderExplorerTree('');

        if (selectedFile) {
          openFile(selectedFile);
        }
      } catch (err) {
        document.getElementById('explorer-tree').innerHTML = `<div style="padding:1rem; color:red;">Failed to load files: ${err.message}</div>`;
      }
    }

    // Open & Render Markdown Document
    async function openFile(relPath) {
      currentFile = relPath;
      const url = new URL(window.location);
      url.searchParams.set('file', relPath);
      window.history.replaceState({}, '', url);

      // Auto-expand parent folders of this file if currently collapsed
      const parts = relPath.split('/');
      let needReRender = false;
      for (let i = 1; i < parts.length; i++) {
        const parentPath = parts.slice(0, i).join('/');
        if (collapsedFolders.has(parentPath)) {
          collapsedFolders.delete(parentPath);
          needReRender = true;
        }
      }
      if (needReRender) {
        renderExplorerTree(document.getElementById('search-input').value.toLowerCase().trim());
      }

      // Highlight active file in explorer tree
      document.querySelectorAll('.file-row').forEach(el => {
        el.classList.toggle('active', el.querySelector('.tree-label')?.title === relPath);
      });

      document.getElementById('preview-path').textContent = relPath;
      document.getElementById('btn-copy').style.display = 'inline-flex';

      const viewer = document.getElementById('markdown-viewer');
      viewer.innerHTML = '<p style="color:var(--text-secondary); text-align:center; padding:2rem;">Loading markdown...</p>';

      try {
        const res = await fetch('/api/content?file=' + encodeURIComponent(relPath));
        if (!res.ok) throw new Error('Status ' + res.status);
        const mdText = await res.text();
        currentRaw = mdText;

        // Render Markdown with marked.js or fallback parser
        let htmlContent = '';
        if (typeof marked !== 'undefined') {
          htmlContent = marked.parse(mdText);
        } else {
          htmlContent = fallbackParseMarkdown(mdText);
        }

        // Apply GitHub alert styling
        htmlContent = transformAlerts(htmlContent);
        viewer.innerHTML = htmlContent;

        // Render Mermaid Diagrams
        if (typeof mermaid !== 'undefined') {
          const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
          mermaid.initialize({
            startOnLoad: false,
            theme: isDark ? 'dark' : 'default',
            securityLevel: 'loose',
            themeVariables: isDark ? {
              darkMode: true,
              actorBkg: '#1e293b',
              actorBorder: '#60a5fa',
              actorTextColor: '#f8fafc',
              actorLineColor: '#94a3b8',
              signalColor: '#94a3b8',
              signalTextColor: '#f1f5f9',
              labelBoxBkgColor: '#334155',
              labelBoxBorderColor: '#94a3b8',
              labelTextColor: '#f8fafc',
              loopTextColor: '#93c5fd',
              noteBkgColor: '#422006',
              noteBorderColor: '#f59e0b',
              noteTextColor: '#fef08a',
              sequenceNumberColor: '#ffffff'
            } : {
              darkMode: false,
              actorBkg: '#f0f7ff',
              actorBorder: '#2563eb',
              actorTextColor: '#1e3a8a',
              actorLineColor: '#64748b',
              signalColor: '#1e293b',
              signalTextColor: '#0f172a',
              labelBoxBkgColor: '#e2e8f0',
              labelBoxBorderColor: '#64748b',
              labelTextColor: '#0f172a',
              loopTextColor: '#1e40af',
              noteBkgColor: '#fef9c3',
              noteBorderColor: '#eab308',
              noteTextColor: '#78350f',
              sequenceNumberColor: '#ffffff'
            }
          });

          const mermaidNodes = viewer.querySelectorAll('.mermaid');
          if (mermaidNodes.length > 0) {
            try {
              await mermaid.run({ nodes: mermaidNodes });
              // Post-process SVG to guarantee lifeline and connector visibility
              viewer.querySelectorAll('.mermaid svg').forEach(svg => {
                svg.querySelectorAll('.actor-line, line[class*="actor-line"]').forEach(line => {
                  line.style.visibility = 'visible';
                  line.style.display = 'block';
                  line.removeAttribute('stroke-opacity');
                  if (!line.getAttribute('stroke') || line.getAttribute('stroke') === 'none') {
                    line.setAttribute('stroke', isDark ? '#94a3b8' : '#64748b');
                  }
                });
                svg.querySelectorAll('.loopLine, line[class*="loopLine"]').forEach(line => {
                  line.style.visibility = 'visible';
                  line.removeAttribute('stroke-opacity');
                  if (!line.getAttribute('stroke') || line.getAttribute('stroke') === 'none') {
                    line.setAttribute('stroke', isDark ? '#94a3b8' : '#64748b');
                  }
                });
              });
            } catch (merr) {
              console.warn("Mermaid rendering warning:", merr);
            }
          }
        }

        // Resolve relative paths based on current markdown file location
        function resolveRelativePath(baseFile, targetPath) {
          if (!targetPath) return targetPath;
          if (/^(https?:|data:|blob:|\/\/|#)/i.test(targetPath)) return targetPath;
          if (targetPath.startsWith('/')) {
            return targetPath.substring(1);
          }
          const baseParts = baseFile.split('/');
          baseParts.pop();
          const targetParts = targetPath.split('/');
          for (const part of targetParts) {
            if (part === '.' || part === '') continue;
            if (part === '..') {
              if (baseParts.length > 0) baseParts.pop();
            } else {
              baseParts.push(part);
            }
          }
          return baseParts.join('/');
        }

        // Transform relative images to /api/raw?file=...
        viewer.querySelectorAll('img').forEach(img => {
          const rawSrc = img.getAttribute('src');
          if (rawSrc && !/^(https?:|data:|blob:|\/\/)/i.test(rawSrc)) {
            const resolved = resolveRelativePath(relPath, rawSrc);
            img.src = '/api/raw?file=' + encodeURIComponent(resolved);
            img.title = img.title || img.alt || 'Double-click to enlarge in Inspector';
            img.style.cursor = 'zoom-in';
          }
        });

        // Intercept markdown links for seamless browsing
        viewer.querySelectorAll('a').forEach(a => {
          const rawHref = a.getAttribute('href');
          if (!rawHref) return;

          // In-page anchor link (#...)
          if (rawHref.startsWith('#')) {
            a.addEventListener('click', (ev) => {
              ev.preventDefault();
              const targetId = rawHref.substring(1);
              const targetEl = document.getElementById(targetId) || 
                               Array.from(viewer.querySelectorAll('h1, h2, h3, h4, h5, h6'))
                                    .find(h => h.textContent.trim().toLowerCase().replace(/[^\w]+/g, '-') === targetId.toLowerCase());
              if (targetEl) targetEl.scrollIntoView({ behavior: 'smooth' });
            });
            return;
          }

          // External web link
          if (/^(https?:|\/\/|mailto:)/i.test(rawHref)) {
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            return;
          }

          // Local file link (e.g. package.json or other.md)
          a.addEventListener('click', (ev) => {
            ev.preventDefault();
            const resolved = resolveRelativePath(relPath, rawHref);
            if (resolved.toLowerCase().endsWith('.md') || resolved.toLowerCase().endsWith('.markdown')) {
              openFile(resolved);
            } else {
              window.open('/api/raw?file=' + encodeURIComponent(resolved), '_blank');
            }
          });
        });

        // Syntax highlight any remaining code blocks
        if (typeof hljs !== 'undefined') {
          viewer.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
        }

        // Build outline
        generateTOC();

        // Scroll viewer to top
        document.getElementById('scroll-container').scrollTop = 0;
      } catch (err) {
        viewer.innerHTML = `<div style="color:#e11d48; padding:2rem;"><h3>Error Loading File</h3><p>${err.message}</p></div>`;
      }
    }
