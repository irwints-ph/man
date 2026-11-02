// Register ABAP language definition for Highlight.js (offline, zero external dependency)
    function registerAbapLanguage() {
      if (typeof hljs === 'undefined') return;
      if (hljs.getLanguage && hljs.getLanguage('abap')) return;

      const abapDef = function(hljsRef) {
        return {
          name: 'ABAP',
          case_insensitive: true,
          keywords: {
            keyword:
              'report program function-pool class endclass interface endinterface ' +
              'definition implementation public protected private section ' +
              'method endmethod form endform function endfunction perform ' +
              'call function method screens module endmodule ' +
              'data types constants statics tables field-symbols parameters select-options ' +
              'type like ref to table of standard sorted hashed with header line ' +
              'initial size range of structure value default ' +
              'if else elseif endif case when endcase while endwhile do enddo ' +
              'check exit return continue try catch endtry cleanup raise message ' +
              'loop at endloop read table where with key into assigning modifying transporting ' +
              'append insert delete clear refresh free sort by lines ' +
              'select single from fields inner left outer join on group order ' +
              'commit rollback work update modify ' +
              'exporting importing changing tables exceptions others returning ' +
              'create object concatenate split replace find condense translate',
            literal:
              'abap_true abap_false space null initial true false x',
            built_in:
              'sy-subrc sy-uname sy-datum sy-uzeit sy-tabix sy-index sy-mandt ' +
              'sy-msgid sy-msgno sy-msgty sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4 sy-dbcnt sy-langu ' +
              'sy-batch sy-tcode sy-repid sy-cprog sy-dynnr'
          },
          contains: [
            {
              className: 'string',
              variants: [
                hljsRef.APOS_STRING_MODE,
                { begin: /`/, end: /`/ }
              ]
            },
            {
              className: 'comment',
              variants: [
                hljsRef.COMMENT(/^[*]/, /$/),
                hljsRef.COMMENT(/"/, /$/)
              ]
            },
            {
              className: 'number',
              begin: '\\b\\d+\\b'
            },
            {
              className: 'symbol',
              begin: /#\w+|@\w+/
            }
          ]
        };
      };

      hljs.registerLanguage('abap', abapDef);
      hljs.registerLanguage('sap-abap', abapDef);
    }

    // Register PowerShell language definition for Highlight.js
    function registerPowershellLanguage() {
      if (typeof hljs === 'undefined') return;
      if (hljs.getLanguage && hljs.getLanguage('powershell')) return;

      const psDef = function(hljsRef) {
        return {
          name: 'PowerShell',
          aliases: ['ps', 'ps1', 'psm1', 'psd1'],
          case_insensitive: true,
          keywords: {
            keyword:
              'if else elseif switch default for foreach in while do until break continue ' +
              'return try catch finally throw trap exit param begin process end dynamicparam ' +
              'function filter configuration workflow class enum using data',
            built_in:
              'Write-Host Write-Output Write-Error Write-Warning Write-Verbose Get-Command ' +
              'Get-Item Get-ChildItem Set-Item New-Item Remove-Item Copy-Item Move-Item ' +
              'Get-Content Set-Content Add-Content Clear-Content Test-Path Out-Null Select-Object ' +
              'Where-Object ForEach-Object Measure-Object Sort-Object Group-Object Start-Process ' +
              'Stop-Process Wait-Process Get-Process Get-Service Start-Service Stop-Service ' +
              'Invoke-WebRequest Invoke-RestMethod ConvertTo-Json ConvertFrom-Json',
            literal: '$true $false $null'
          },
          contains: [
            {
              className: 'variable',
              begin: /\$([a-zA-Z0-9_:]+|\{[^}]+\})/
            },
            hljsRef.COMMENT(/#/, /$/),
            hljsRef.COMMENT(/<#/, /#>/),
            hljsRef.QUOTE_STRING_MODE,
            hljsRef.APOS_STRING_MODE,
            hljsRef.NUMBER_MODE
          ]
        };
      };

      hljs.registerLanguage('powershell', psDef);
      hljs.registerLanguage('ps1', psDef);
    }

    // Configure Marked with Mermaid custom renderer
    function setupMarked() {
      if (typeof marked === 'undefined') return;
      registerAbapLanguage();
      registerPowershellLanguage();

      const renderer = new marked.Renderer();
      const origCodeRenderer = renderer.code.bind(renderer);

      renderer.code = function(code, language, isEscaped) {
        if (language === 'mermaid') {
          const id = 'mermaid-' + Math.random().toString(36).substring(2, 9);
          // Escape raw code for safe DOM storage
          const safeCode = code
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

          return `
            <div class="mermaid-wrapper" data-mermaid-id="${id}" title="Double click diagram to enlarge">
              <div class="mermaid-toolbar">
                <span style="font-weight:600;">📊 Mermaid Diagram</span>
                <span class="mermaid-hint">Double-click to enlarge 🔍</span>
                <button type="button" class="btn btn-sm" onclick="enlargeMermaid('${id}', event)" title="Enlarge diagram in full modal">⛶ Enlarge</button>
              </div>
              <div class="mermaid-viewport" id="vp-${id}">
                <div class="mermaid" id="${id}">${safeCode}</div>
              </div>
            </div>
          `;
        }
        return origCodeRenderer(code, language, isEscaped);
      };

      marked.setOptions({
        renderer: renderer,
        gfm: true,
        breaks: true,
        highlight: function(code, lang) {
          if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
          }
          return code;
        }
      });
    }

    // GitHub Alert Transformer
    function transformAlerts(html) {
      const alertTypes = ['NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION'];
      const icons = {
        NOTE: 'ℹ️',
        TIP: '💡',
        IMPORTANT: '🔔',
        WARNING: '⚠️',
        CAUTION: '🛑'
      };

      for (const type of alertTypes) {
        const regex = new RegExp(`<blockquote>\\s*<p>\\s*\\[!${type}\\](.*?)(<\\/p>\\s*<\\/blockquote>|<\\/blockquote>)`, 'gis');
        html = html.replace(regex, (match, body) => {
          return `<div class="markdown-alert markdown-alert-${type.toLowerCase()}">
            <div class="markdown-alert-title">${icons[type]} ${type}</div>
            <p>${body.trim()}</p>
          </div>`;
        });
      }
      return html;
    }

    // Build Table of Contents & Code Outline
    function generateTOC() {
      const viewer = document.getElementById('markdown-viewer');
      const headers = viewer.querySelectorAll('h1, h2, h3, h4');
      const tocList = document.getElementById('toc-list');
      tocList.innerHTML = '';

      if (headers.length > 0) {
        headers.forEach((header, idx) => {
          const id = 'heading-' + idx;
          header.id = id;
          const li = document.createElement('li');
          const level = parseInt(header.tagName.substring(1));
          li.style.paddingLeft = ((level - 1) * 0.75) + 'rem';
          const a = document.createElement('a');
          a.href = '#' + id;
          a.textContent = header.textContent;
          a.onclick = (ev) => {
            ev.preventDefault();
            header.scrollIntoView({ behavior: 'smooth' });
            tocDrawer.classList.remove('open');
          };
          li.appendChild(a);
          tocList.appendChild(li);
        });
        return;
      }

      // If no headings found, inspect code file for structural comment blocks or definitions
      if (currentRaw && currentFile) {
        const ext = currentFile.includes('.') ? currentFile.split('.').pop().toLowerCase() : '';
        const lines = currentRaw.split('\n');
        const items = [];

        lines.forEach((line, lineIdx) => {
          const trimmed = line.trim();
          if (ext === 'sql') {
            if (/^--\s*([A-Za-z0-9].*)/.test(trimmed)) {
              const text = trimmed.replace(/^--\s*/, '').replace(/[-=*_]{3,}$/, '').trim();
              if (text && text.length > 2 && text.length < 80) items.push({ text: '💬 ' + text, lineIdx });
            } else if (/^\/\*\s*([A-Za-z0-9].*)/.test(trimmed)) {
              const text = trimmed.replace(/^\/\*\s*/, '').replace(/\*\/$/, '').trim();
              if (text && text.length > 2 && text.length < 80) items.push({ text: '📌 ' + text, lineIdx });
            } else if (/^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)/i.test(trimmed)) {
              const m = trimmed.match(/^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)/i);
              items.push({ text: '🗄️ CREATE TABLE ' + m[1], lineIdx });
            } else if (/^WITH\s+([a-zA-Z0-9_]+)\s+AS/i.test(trimmed)) {
              const m = trimmed.match(/^WITH\s+([a-zA-Z0-9_]+)\s+AS/i);
              items.push({ text: '⚡ WITH ' + m[1], lineIdx });
            }
          } else if (ext === 'py') {
            if (/^(?:def|class)\s+([a-zA-Z0-9_]+)/.test(trimmed)) {
              const m = trimmed.match(/^(def|class)\s+([a-zA-Z0-9_]+)/);
              items.push({ text: (m[1] === 'class' ? '🔷 ' : '⚡ ') + m[0], lineIdx });
            }
          }
        });

        if (items.length > 0) {
          items.forEach((item) => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = item.text;
            a.onclick = (ev) => {
              ev.preventDefault();
              const codeEl = viewer.querySelector('pre');
              if (codeEl) {
                codeEl.scrollTop = (item.lineIdx / lines.length) * codeEl.scrollHeight;
              }
              tocDrawer.classList.remove('open');
            };
            li.appendChild(a);
            tocList.appendChild(li);
          });
          return;
        }
      }

      tocList.innerHTML = '<li style="color:var(--text-secondary)">No headings found</li>';
    }

    // Minimal Offline Fallback Markdown Parser
    function fallbackParseMarkdown(text) {
      return text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\\*\\*(.*)\\*\\*/gim, '<b>$1</b>')
        .replace(/\\*(.*)\\*/gim, '<i>$1</i>')
        .replace(/```([\\s\\S]*?)```/gim, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/gim, '<code>$1</code>')
        .replace(/\\n/gim, '<br />');
    }

    function copyRawContent() {
      if (!currentRaw) return;
      navigator.clipboard.writeText(currentRaw).then(() => {
        const btn = document.getElementById('btn-copy');
        const orig = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => { btn.textContent = orig; }, 1800);
      });
    }
