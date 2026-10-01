// Search filter
    document.getElementById('search-input').addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      isSearchActive = query.length > 0;
      renderExplorerTree(query);
    });

    // Build Hierarchical Tree from flat paths
    function buildTree(files) {
      const root = { name: '', type: 'folder', path: '', children: {} };

      files.forEach(file => {
        const parts = file.path.split('/');
        let curr = root;

        for (let i = 0; i < parts.length - 1; i++) {
          const folderName = parts[i];
          const folderPath = parts.slice(0, i + 1).join('/');
          if (!curr.children[folderName]) {
            curr.children[folderName] = {
              name: folderName,
              type: 'folder',
              path: folderPath,
              children: {}
            };
          }
          curr = curr.children[folderName];
        }

        const fileName = parts[parts.length - 1];
        curr.children[fileName] = {
          name: fileName,
          type: 'file',
          path: file.path,
          size: file.size
        };
      });

      return root;
    }

    function countFiles(node) {
      if (node.type === 'file') return 1;
      let count = 0;
      for (const key in node.children) {
        count += countFiles(node.children[key]);
      }
      return count;
    }

    // Render Explorer Tree
    function renderExplorerTree(filterQuery = '') {
      const treeContainer = document.getElementById('explorer-tree');
      treeContainer.innerHTML = '';

      const tree = buildTree(rawFilesList);

      function renderNode(node) {
        const sortedKeys = Object.keys(node.children).sort((a, b) => {
          const nodeA = node.children[a];
          const nodeB = node.children[b];
          if (nodeA.type !== nodeB.type) return nodeA.type === 'folder' ? -1 : 1;
          return a.localeCompare(b);
        });

        const fragment = document.createDocumentFragment();

        sortedKeys.forEach(key => {
          const item = node.children[key];

          if (item.type === 'folder') {
            const folderCount = countFiles(item);
            // If search active, check if any descendant matches
            if (filterQuery) {
              const matchesDescendant = (n) => {
                if (n.type === 'file') return n.name.toLowerCase().includes(filterQuery) || n.path.toLowerCase().includes(filterQuery);
                return Object.values(n.children).some(matchesDescendant);
              };
              if (!matchesDescendant(item)) return;
            }

            const folderDiv = document.createElement('div');
            const isCollapsed = !isSearchActive && collapsedFolders.has(item.path);
            folderDiv.className = 'tree-folder' + (isCollapsed ? ' collapsed' : '');

            const row = document.createElement('div');
            row.className = 'tree-row folder-row';
            row.onclick = (e) => {
              e.stopPropagation();
              folderDiv.classList.toggle('collapsed');
              if (folderDiv.classList.contains('collapsed')) {
                collapsedFolders.add(item.path);
              } else {
                collapsedFolders.delete(item.path);
              }
            };

            const chevron = document.createElement('span');
            chevron.className = 'tree-chevron';
            chevron.textContent = '▾';

            const icon = document.createElement('span');
            icon.className = 'tree-icon';
            icon.textContent = folderDiv.classList.contains('collapsed') ? '📁' : '📂';

            const label = document.createElement('span');
            label.className = 'tree-label';
            label.textContent = item.name;

            const badge = document.createElement('span');
            badge.className = 'tree-count-badge';
            badge.textContent = folderCount;

            row.appendChild(chevron);
            row.appendChild(icon);
            row.appendChild(label);
            row.appendChild(badge);
            folderDiv.appendChild(row);

            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';
            childrenContainer.appendChild(renderNode(item));
            folderDiv.appendChild(childrenContainer);

            fragment.appendChild(folderDiv);
          } else {
            // File item
            if (filterQuery && !item.name.toLowerCase().includes(filterQuery) && !item.path.toLowerCase().includes(filterQuery)) {
              return;
            }

            const fileRow = document.createElement('div');
            fileRow.className = 'tree-row file-row' + (currentFile === item.path ? ' active' : '');
            fileRow.onclick = (e) => {
              e.stopPropagation();
              openFile(item.path);
              if (window.innerWidth < 768) sidebar.classList.remove('open');
            };

            const chevronSpacer = document.createElement('span');
            chevronSpacer.style.width = '16px';
            chevronSpacer.style.marginRight = '0.25rem';
            chevronSpacer.style.display = 'inline-block';

            const icon = document.createElement('span');
            icon.className = 'tree-icon';
            icon.textContent = '📄';

            const label = document.createElement('span');
            label.className = 'tree-label';
            label.textContent = item.name;
            label.title = item.path;

            const size = document.createElement('span');
            size.className = 'tree-file-size';
            size.textContent = (item.size / 1024).toFixed(1) + ' KB';

            fileRow.appendChild(chevronSpacer);
            fileRow.appendChild(icon);
            fileRow.appendChild(label);
            fileRow.appendChild(size);
            fragment.appendChild(fileRow);
          }
        });

        return fragment;
      }

      const renderedTree = renderNode(tree);
      if (renderedTree.children.length === 0) {
        treeContainer.innerHTML = '<div style="padding:1rem; font-size:0.8rem; color:var(--text-secondary); text-align:center;">No matching files found</div>';
      } else {
        treeContainer.appendChild(renderedTree);
      }
    }

    function expandAllFolders(expand) {
      if (expand) {
        collapsedFolders.clear();
      } else {
        // Collect all folder paths
        function collect(files) {
          files.forEach(f => {
            const parts = f.path.split('/');
            for (let i = 1; i < parts.length; i++) {
              collapsedFolders.add(parts.slice(0, i).join('/'));
            }
          });
        }
        collect(rawFilesList);
      }
      renderExplorerTree(document.getElementById('search-input').value.toLowerCase().trim());
    }
