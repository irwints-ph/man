// Lightbox Pan & Zoom State
    let lbZoom = 1.0;
    let lbPanX = 0;
    let lbPanY = 0;
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let lbNaturalW = 800;
    let lbNaturalH = 600;

    // Double-Click Delegated Handler for Mermaid Diagrams & Images
    document.getElementById('markdown-viewer').addEventListener('dblclick', (e) => {
      // Check for mermaid diagram
      const mermaidWrapper = e.target.closest('.mermaid-wrapper');
      if (mermaidWrapper) {
        const svg = mermaidWrapper.querySelector('svg');
        if (svg) {
          openMermaidInLightbox(svg);
          return;
        }
      }

      // Check for images
      if (e.target.tagName === 'IMG') {
        const natW = e.target.naturalWidth || e.target.width || 800;
        const natH = e.target.naturalHeight || e.target.height || 600;
        const img = document.createElement('img');
        img.src = e.target.src;
        img.alt = e.target.alt || 'Image Inspector';
        openLightbox(img, e.target.alt || 'Image Inspector', natW, natH);
      }
    });

    // Enlarge button on Mermaid toolbar
    function enlargeMermaid(id, event) {
      if (event) event.stopPropagation();
      const container = document.getElementById(id);
      if (container) {
        const svg = container.querySelector('svg') || (container.tagName && container.tagName.toLowerCase() === 'svg' ? container : null);
        if (svg) {
          openMermaidInLightbox(svg);
        }
      }
    }

    function openMermaidInLightbox(svgElement) {
      const origId = svgElement.id;
      const newId = 'lb-' + Math.random().toString(36).substring(2, 9);
      const cloned = svgElement.cloneNode(true);
      cloned.id = newId;

      if (origId) {
        // Rewrite all ID references in a single clean pass so styles, markers, and gradients remain 100% valid
        try {
          const serialized = new XMLSerializer().serializeToString(cloned);
          const replaced = serialized.replaceAll(origId, newId);
          const doc = new DOMParser().parseFromString(replaced, 'image/svg+xml');
          const finalSvg = doc.documentElement;
          openLightbox(finalSvg, 'Mermaid Diagram Inspector');
          return;
        } catch (e) {
          console.warn("SVG XMLSerializer fallback:", e);
        }
      }

      openLightbox(cloned, 'Mermaid Diagram Inspector');
    }

    // Lightbox Modal Controls
    const lbModal = document.getElementById('lightbox-modal');
    const lbStage = document.getElementById('lightbox-stage');

    function openLightbox(contentNodeOrHtml, title = 'Diagram Inspector', initialW = 0, initialH = 0) {
      lbStage.innerHTML = '';
      const card = document.createElement('div');
      card.className = 'lightbox-card';

      if (typeof contentNodeOrHtml === 'string') {
        card.innerHTML = contentNodeOrHtml;
      } else if (contentNodeOrHtml instanceof Node) {
        card.appendChild(contentNodeOrHtml);
      }
      lbStage.appendChild(card);

      const svg = card.querySelector('svg');
      if (svg) {
        svg.style.maxWidth = 'none';
        svg.style.maxHeight = 'none';

        // Read unconstrained viewBox dimensions
        const vb = svg.getAttribute('viewBox');
        if (vb) {
          const parts = vb.split(/[\s,]+/).filter(Boolean);
          if (parts.length === 4) {
            lbNaturalW = parseFloat(parts[2]) || 800;
            lbNaturalH = parseFloat(parts[3]) || 600;
          }
        } else {
          const bbox = svg.getBoundingClientRect();
          lbNaturalW = bbox.width || 800;
          lbNaturalH = bbox.height || 600;
        }

        // Set native dimensions on SVG so it renders 100% sharp
        svg.style.width = lbNaturalW + 'px';
        svg.style.height = lbNaturalH + 'px';
        svg.setAttribute('width', lbNaturalW);
        svg.setAttribute('height', lbNaturalH);
      } else {
        const img = card.querySelector('img');
        if (img) {
          lbNaturalW = initialW || img.naturalWidth || img.width || 800;
          lbNaturalH = initialH || img.naturalHeight || img.height || 600;
          img.style.maxWidth = 'none';
          img.style.maxHeight = 'none';
          img.style.width = lbNaturalW + 'px';
          img.style.height = lbNaturalH + 'px';
        }
      }

      const titleEl = document.getElementById('lb-title-text');
      if (titleEl) titleEl.textContent = '🔍 ' + title;

      fitLightbox();
      lbModal.classList.add('open');
    }

    function closeLightbox() {
      lbModal.classList.remove('open');
      lbStage.innerHTML = '';
    }

    function fitLightbox() {
      const availW = window.innerWidth * 0.88;
      const availH = (window.innerHeight - 70) * 0.84;
      const ratioW = availW / Math.max(lbNaturalW, 100);
      const ratioH = availH / Math.max(lbNaturalH, 100);
      lbZoom = Math.min(ratioW, ratioH, 1.0);
      lbZoom = Math.max(Math.round(lbZoom * 100) / 100, 0.15);
      lbPanX = 0;
      lbPanY = 0;
      updateLightboxTransform();
    }

    function resetLightboxZoom() {
      lbZoom = 1.0;
      lbPanX = 0;
      lbPanY = 0;
      updateLightboxTransform();
    }

    function zoomLightbox(factor) {
      lbZoom = Math.min(Math.max(Math.round(lbZoom * factor * 100) / 100, 0.15), 8.0);
      updateLightboxTransform();
    }

    function updateLightboxTransform() {
      lbStage.style.transform = `translate(calc(-50% + ${lbPanX}px), calc(-50% + ${lbPanY}px)) scale(${lbZoom})`;
      const badge = document.getElementById('lb-zoom-badge');
      if (badge) badge.textContent = `${Math.round(lbZoom * 100)}%`;
    }

    // Download SVG from lightbox
    function downloadLightboxSvg() {
      const svg = lbStage.querySelector('svg');
      if (!svg) return;
      const svgData = new XMLSerializer().serializeToString(svg);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const svgUrl = URL.createObjectURL(svgBlob);
      const a = document.createElement('a');
      a.href = svgUrl;
      a.download = 'diagram-' + Date.now() + '.svg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(svgUrl);
    }

    // Lightbox Pan & Zoom interaction (drag + wheel)
    const lbBody = document.getElementById('lightbox-body');

    lbBody.addEventListener('wheel', (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      zoomLightbox(factor);
    }, { passive: false });

    lbBody.addEventListener('mousedown', (e) => {
      if (e.target.closest('.lightbox-btn')) return;
      isDragging = true;
      dragStartX = e.clientX - lbPanX;
      dragStartY = e.clientY - lbPanY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      lbPanX = e.clientX - dragStartX;
      lbPanY = e.clientY - dragStartY;
      updateLightboxTransform();
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });
