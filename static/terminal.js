(function () {
  'use strict';

  var MAX_HISTORY = 50;
  var TYPEWRITER_CHUNK = 4;
  var TYPEWRITER_DELAY = 8;

  document.addEventListener('DOMContentLoaded', function () {
    var input  = document.getElementById('query-input');
    var output = document.getElementById('output');
    if (!input || !output) return;

    var history      = [];
    var historyIndex = -1;
    var pendingSave  = '';
    var busy         = false;

    input.focus();

    document.addEventListener('click', function (e) {
      var tag = e.target.tagName;
      if (tag !== 'A' && tag !== 'BUTTON' && tag !== 'INPUT') {
        input.focus();
      }
    });

    input.addEventListener('keydown', function (e) {
      if (busy) return;

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (historyIndex === -1) pendingSave = input.value;
        if (historyIndex < history.length - 1) {
          historyIndex++;
          input.value = history[historyIndex];
          deferCursorToEnd(input);
        }
        return;
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (historyIndex > 0) {
          historyIndex--;
          input.value = history[historyIndex];
        } else if (historyIndex === 0) {
          historyIndex = -1;
          input.value = pendingSave;
        }
        deferCursorToEnd(input);
        return;
      }

      if (e.key === 'Escape') {
        input.value  = '';
        historyIndex = -1;
        pendingSave  = '';
        return;
      }

      if (e.key === 'Enter') {
        var query = input.value.trim();
        if (!query) return;

        input.value  = '';
        historyIndex = -1;
        pendingSave  = '';

        if (history[0] !== query) {
          history.unshift(query);
          if (history.length > MAX_HISTORY) history.pop();
        }

        appendQueryLine(query);
        runQuery(query);
      }
    });

    function deferCursorToEnd(el) {
      var len = el.value.length;
      requestAnimationFrame(function () { el.setSelectionRange(len, len); });
    }

    function appendQueryLine(query) {
      var div = document.createElement('div');
      div.className = 'query-line';
      div.textContent = '> ' + query;
      output.appendChild(div);
      scrollOutput();
    }

    async function runQuery(query) {
      busy = true;
      input.disabled = true;

      var loadingEl = createLoadingEl();
      output.appendChild(loadingEl);
      scrollOutput();

      try {
        var response = await fetch('/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query }),
        });

        loadingEl.remove();

        if (!response.ok) {
          var errData = await response.json().catch(function () { return {}; });
          appendErrorLine('[ERROR ' + response.status + ']: ' + (errData.detail || 'Request failed.'));
          return;
        }

        var data = await response.json();
        await typeAnswer(data.answer || '(no answer)');

        if (data.sources && data.sources.length > 0) {
          appendSourcesLine(data.sources);
        }

        scrollOutput();
      } catch (err) {
        loadingEl.remove();
        appendErrorLine('[NETWORK ERROR]: ' + err.message);
      } finally {
        busy = false;
        input.disabled = false;
        input.focus();
      }
    }

    function createLoadingEl() {
      var div = document.createElement('div');
      div.className = 'answer-line loading-dots';
      div.setAttribute('aria-label', 'Processing');
      div.textContent = 'PROCESSING';
      return div;
    }

    async function typeAnswer(text) {
      var div = document.createElement('div');
      div.className = 'answer-line';
      output.appendChild(div);

      for (var i = 0; i < text.length; i += TYPEWRITER_CHUNK) {
        div.textContent += text.slice(i, i + TYPEWRITER_CHUNK);
        if (i % (TYPEWRITER_CHUNK * 10) === 0) scrollOutput();
        await sleep(TYPEWRITER_DELAY);
      }
      scrollOutput();
    }

    function appendSourcesLine(sources) {
      var wrap = document.createElement('div');
      wrap.className = 'sources-line';
      wrap.appendChild(document.createTextNode('[SOURCES]: '));

      sources.forEach(function (slug) {
        var a = document.createElement('a');
        a.href = '/doc/' + encodeURIComponent(slug);
        a.className = 'source-link';
        a.textContent = slug;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        wrap.appendChild(a);
        wrap.appendChild(document.createTextNode(' '));
      });

      output.appendChild(wrap);
    }

    function appendErrorLine(msg) {
      var div = document.createElement('div');
      div.className = 'error-line';
      div.textContent = msg;
      output.appendChild(div);
      scrollOutput();
    }

    function scrollOutput() {
      output.scrollTop = output.scrollHeight;
    }

    function sleep(ms) {
      return new Promise(function (r) { setTimeout(r, ms); });
    }
  });
})();
