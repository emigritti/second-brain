(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', async function () {
    var cyEl   = document.getElementById('cy');
    var infoEl = document.getElementById('graph-info');
    if (!cyEl) return;

    var cy = null;

    var elements;
    try {
      var res = await fetch('/graph/data');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      elements = await res.json();
    } catch (err) {
      console.error('Graph load failed:', err);
      showEmptyState('GRAPH DATA UNAVAILABLE', err.message);
      return;
    }

    var hasNodes = elements &&
      ((Array.isArray(elements) && elements.length > 0) ||
       (elements.nodes && elements.nodes.length > 0));

    if (!hasNodes) {
      showEmptyState('NO DOCUMENTS INDEXED', 'Upload a PDF to populate the graph.');
      return;
    }

    cy = cytoscape({
      container: cyEl,
      elements: elements,
      style: buildStyles(),
      layout: { name: 'cose', animate: false, padding: 60, nodeRepulsion: 4096 },
      minZoom: 0.1,
      maxZoom: 5,
    });

    // Node tap → show info panel
    cy.on('tap', 'node', function (evt) {
      showNodeInfo(evt.target);
    });

    // Background tap → hide info panel
    cy.on('tap', function (evt) {
      if (evt.target === cy) hideNodeInfo();
    });

    // Zoom controls
    var midX = function () { return cyEl.clientWidth  / 2; };
    var midY = function () { return cyEl.clientHeight / 2; };

    document.getElementById('btn-zoom-in')?.addEventListener('click', function () {
      cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: midX(), y: midY() } });
    });
    document.getElementById('btn-zoom-out')?.addEventListener('click', function () {
      cy.zoom({ level: cy.zoom() * 0.75, renderedPosition: { x: midX(), y: midY() } });
    });
    document.getElementById('btn-zoom-fit')?.addEventListener('click', function () {
      cy.fit(undefined, 40);
    });

    // Close button on info panel
    document.getElementById('graph-info-close')?.addEventListener('click', hideNodeInfo);

    // Node search / filter
    var searchInput = document.getElementById('graph-search');
    if (searchInput) {
      var searchTimer = null;
      searchInput.addEventListener('input', function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(function () {
          var q = searchInput.value.trim().toLowerCase();
          if (!q) {
            cy.nodes().removeClass('dim highlighted');
            cy.edges().removeClass('dim');
            return;
          }
          cy.nodes().forEach(function (node) {
            var title = String(node.data('title') || node.id()).toLowerCase();
            if (title.includes(q)) {
              node.removeClass('dim').addClass('highlighted');
            } else {
              node.addClass('dim').removeClass('highlighted');
            }
          });
          cy.edges().addClass('dim');
        }, 180);
      });

      searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          searchInput.value = '';
          cy.nodes().removeClass('dim highlighted');
          cy.edges().removeClass('dim');
        }
      });
    }

    function buildStyles() {
      return [
        {
          selector: 'node',
          style: {
            'background-color': '#33ff33',
            'border-width': 0,
            'label': 'data(title)',
            'color': '#cccccc',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 7,
            'text-outline-color': '#050505',
            'text-outline-width': 3,
            'font-family': 'JetBrains Mono, monospace',
            'font-size': 10,
            'width': 14,
            'height': 14,
          },
        },
        {
          selector: 'node[?is_dangling]',
          style: {
            'background-color': '#1a5c1a',
            'border-width': 1,
            'border-color': '#33ff33',
            'border-style': 'dashed',
          },
        },
        {
          selector: 'node:selected, node.highlighted',
          style: {
            'background-color': '#ffffff',
            'width': 20,
            'height': 20,
            'color': '#33ff33',
          },
        },
        {
          selector: 'node.dim',
          style: { 'opacity': 0.12 },
        },
        /* Edge type coloring */
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': '#1a5c1a',
            'target-arrow-color': '#1a5c1a',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.6,
            'arrow-scale': 0.7,
          },
        },
        {
          selector: 'edge[type = "wikilink"]',
          style: {
            'line-color': '#33ff33',
            'target-arrow-color': '#33ff33',
          },
        },
        {
          selector: 'edge[type = "tag"]',
          style: {
            'line-color': '#ffb000',
            'target-arrow-color': '#ffb000',
          },
        },
        {
          selector: 'edge[type = "semantic"]',
          style: {
            'line-color': '#00ffcc',
            'target-arrow-color': '#00ffcc',
          },
        },
        {
          selector: 'edge.dim',
          style: { 'opacity': 0.04 },
        },
      ];
    }

    function showNodeInfo(node) {
      var id    = node.id();
      var title = node.data('title') || id;
      var tags  = node.data('tags') || [];
      var connections = node.connectedEdges().length;

      document.getElementById('graph-info-title').textContent = title;

      document.getElementById('graph-info-meta').textContent =
        'slug: ' + id + '\n' + connections + ' connection' + (connections !== 1 ? 's' : '');

      var tagsEl = document.getElementById('graph-info-tags');
      tagsEl.innerHTML = '';
      if (Array.isArray(tags) && tags.length) {
        tags.forEach(function (tag) {
          var span = document.createElement('span');
          span.className = 'graph-tag';
          span.textContent = tag;
          tagsEl.appendChild(span);
        });
      }

      var link = document.getElementById('graph-info-link');
      link.href = '/doc/' + encodeURIComponent(id);

      infoEl.classList.add('visible');
    }

    function hideNodeInfo() {
      if (infoEl) infoEl.classList.remove('visible');
    }

    function showEmptyState(heading, sub) {
      var wrap = document.querySelector('.graph-page') || cyEl.parentElement;
      var div = document.createElement('div');
      div.className = 'graph-empty';
      var h = document.createElement('span');
      h.className = 'graph-empty-heading';
      h.textContent = heading;
      var s = document.createElement('span');
      s.className = 'graph-empty-sub';
      s.textContent = sub;
      div.appendChild(h);
      div.appendChild(s);
      wrap.appendChild(div);
    }
  });
})();
