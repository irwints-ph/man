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
          // Prioritize Markdown or README files in the root folder first
          const rootFiles = rawFilesList.filter(f => !f.path.includes('/'));
          if (rootFiles.length > 0) {
            // Prioritize README.md / readme.md if present among root files
            const readme = rootFiles.find(f => f.name.toLowerCase() === 'readme.md');
            const rootMd = rootFiles.find(f => f.name.toLowerCase().endsWith('.md'));
            selectedFile = readme ? readme.path : (rootMd ? rootMd.path : rootFiles[0].path);
          } else {
            // If none in root folder, open the 1st document inside the folders (prioritizing README if present)
            const readme = rawFilesList.find(f => f.name.toLowerCase() === 'readme.md');
            const mdFile = rawFilesList.find(f => f.name.toLowerCase().endsWith('.md'));
            selectedFile = readme ? readme.path : (mdFile ? mdFile.path : rawFilesList[0].path);
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

    function escapeHtml(text) {
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    // Open & Render Markdown or Code Document
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

      const ext = relPath.includes('.') ? relPath.split('.').pop().toLowerCase() : '';
      const isMarkdown = ext === 'md' || ext === 'markdown';
      const isHtml = ext === 'html' || ext === 'htm';

      document.getElementById('preview-path').textContent = relPath;
      document.getElementById('btn-copy').style.display = 'inline-flex';
      document.getElementById('btn-copy').title = isMarkdown ? 'Copy raw Markdown' : `Copy ${ext.toUpperCase()}`;

      const htmlToggle = document.getElementById('html-view-toggle');
      const btnOpenTab = document.getElementById('btn-open-tab');
      const zoomControls = document.getElementById('zoom-controls');
      const scrollContainer = document.getElementById('scroll-container');

      if (isHtml) {
        if (htmlToggle) htmlToggle.style.display = 'inline-flex';
        if (btnOpenTab) btnOpenTab.style.display = 'inline-flex';
      } else {
        if (htmlToggle) htmlToggle.style.display = 'none';
        if (btnOpenTab) btnOpenTab.style.display = 'none';
        if (zoomControls) zoomControls.style.display = 'inline-flex';
        if (scrollContainer) scrollContainer.classList.remove('iframe-active');
      }

      const viewer = document.getElementById('markdown-viewer');
      viewer.innerHTML = '<p style="color:var(--text-secondary); text-align:center; padding:2rem;">Loading document...</p>';

      try {
        const res = await fetch('/api/content?file=' + encodeURIComponent(relPath));
        if (!res.ok) throw new Error('Status ' + res.status);
        const text = await res.text();
        currentRaw = text;

        if (isHtml) {
          // Render HTML page by default or in source mode
          setHtmlViewMode(currentHtmlMode || 'rendered');
        } else if (isMarkdown) {
          // Render Markdown with marked.js or fallback parser
          let htmlContent = '';
          if (typeof marked !== 'undefined') {
            htmlContent = marked.parse(text);
          } else {
            htmlContent = fallbackParseMarkdown(text);
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
        } else {
          // Render Code / SQL with syntax highlighting
          const langMap = {
            sql: 'sql',
            py: 'python',
            json: 'json',
            js: 'javascript',
            ts: 'typescript',
            html: 'html',
            xml: 'xml',
            css: 'css',
            yaml: 'yaml',
            yml: 'yaml',
            sh: 'bash',
            bash: 'bash',
            bat: 'batch',
            cmd: 'batch',
            ps1: 'powershell',
            psm1: 'powershell',
            psd1: 'powershell',
            txt: 'plaintext',
            log: 'plaintext',
            csv: 'plaintext',
            tsv: 'plaintext'
          };
          const lang = langMap[ext] || 'plaintext';
          const lineCount = text.split('\n').length;
          const safeCode = escapeHtml(text);
          const iconBadge = (typeof getFileIcon === 'function') ? getFileIcon(relPath) : '📄';

          viewer.innerHTML = `
            <div class="code-view-container">
              <div class="code-view-header">
                <span class="code-view-badge">${iconBadge} ${ext.toUpperCase()} Source</span>
                <span class="code-view-meta">${lineCount} lines · ${(new Blob([text]).size / 1024).toFixed(1)} KB</span>
              </div>
              <pre><code class="language-${lang}">${safeCode}</code></pre>
            </div>
          `;
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

          // Local file link (e.g. package.json or question.sql or other.md)
          a.addEventListener('click', (ev) => {
            ev.preventDefault();
            const resolved = resolveRelativePath(relPath, rawHref);
            const lowerResolved = resolved.toLowerCase();
            const isPreviewable = rawFilesList.some(f => f.path.toLowerCase() === lowerResolved) ||
                                  ['.md', '.markdown', '.sql', '.py', '.json', '.txt', '.yaml', '.yml', '.sh', '.bat', '.cmd', '.ps1', '.psm1', '.psd1', '.html', '.htm'].some(e => lowerResolved.endsWith(e));
            if (isPreviewable) {
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

    let currentHtmlMode = 'rendered';

    function openCurrentInNewTab() {
      if (!currentFile) return;
      const isHtml = currentFile.toLowerCase().endsWith('.html') || currentFile.toLowerCase().endsWith('.htm');
      const targetUrl = isHtml ? ('/raw/' + encodeURI(currentFile)) : ('/api/raw?file=' + encodeURIComponent(currentFile));
      window.open(targetUrl, '_blank');
    }

    function setHtmlViewMode(mode) {
      currentHtmlMode = mode;
      const btnRender = document.getElementById('btn-html-render');
      const btnSource = document.getElementById('btn-html-source');
      const zoomControls = document.getElementById('zoom-controls');
      const scrollContainer = document.getElementById('scroll-container');
      const viewer = document.getElementById('markdown-viewer');

      if (!viewer) return;

      if (mode === 'rendered') {
        if (btnRender) btnRender.classList.add('active');
        if (btnSource) btnSource.classList.remove('active');
        if (zoomControls) zoomControls.style.display = 'none';
        if (scrollContainer) scrollContainer.classList.add('iframe-active');
        const rawUrl = '/raw/' + encodeURI(currentFile);
        viewer.innerHTML = `<iframe class="html-preview-frame" src="${rawUrl}" title="HTML Preview"></iframe>`;
      } else {
        if (btnRender) btnRender.classList.remove('active');
        if (btnSource) btnSource.classList.add('active');
        if (zoomControls) zoomControls.style.display = 'inline-flex';
        if (scrollContainer) scrollContainer.classList.remove('iframe-active');
        const text = currentRaw || '';
        const lineCount = text.split('\n').length;
        const safeCode = escapeHtml(text);
        const iconBadge = (typeof getFileIcon === 'function') ? getFileIcon(currentFile) : '🌐';
        viewer.innerHTML = `
          <div class="code-view-container">
            <div class="code-view-header">
              <span class="code-view-badge">${iconBadge} HTML Source</span>
              <span class="code-view-meta">${lineCount} lines · ${(new Blob([text]).size / 1024).toFixed(1)} KB</span>
            </div>
            <pre><code class="language-html">${safeCode}</code></pre>
          </div>
        `;
        if (typeof hljs !== 'undefined') {
          viewer.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
        }
      }
    }
