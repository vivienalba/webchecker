/* Same product interface and API, transported by Streamlit when embedded. */
(() => {
  if (window.parent === window) return;
  // Component iframes may disable document scrolling. Use our own scroll area.
  document.documentElement.classList.add('wqc-streamlit');
  const nativeFetch = window.fetch.bind(window);
  const pending = [], images = new Map(), imageMarker = '#wqc-artifact=';
  const placeholder = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%221%22 height=%221%22%3E%3C/svg%3E';
  let active = null, ready = false, parentOrigin = '*', lastHeight = 0;
  function send(type, data) {
    window.parent.postMessage({isStreamlitMessage: true, type, ...data}, parentOrigin);
  }
  function pump() {
    if (!ready || active || !pending.length) return;
    active = pending.shift();
    send('streamlit:setComponentValue', {value: active.request, dataType: 'json'});
  }
  function rpc(path, options = {}) {
    return new Promise((resolve, reject) => {
      const id = crypto.randomUUID ? crypto.randomUUID() : Date.now() + '-' + Math.random();
      pending.push({request: {id, path, method: options.method || 'GET', body: options.body || ''}, resolve, reject});
      pump();
    });
  }
  window.fetch = (input, options = {}) => {
    const path = typeof input === 'string' ? input : input.url;
    return path.startsWith('/api/') ? rpc(path, options) : nativeFetch(input, options);
  };
  function frameHeight() {
    let height = 850;
    try { height = Math.max(360, window.parent.innerHeight - 2); } catch (_) {}
    if (height !== lastHeight) {
      lastHeight = height;
      send('streamlit:setFrameHeight', {height});
    }
  }
  window.addEventListener('message', event => {
    if (event.source !== window.parent || event.data?.type !== 'streamlit:render') return;
    parentOrigin = event.origin && event.origin !== 'null' ? event.origin : '*';
    ready = true;
    const response = event.data.args?.response;
    if (active && response?.id === active.request.id) {
      const item = active;
      active = null;
      try {
        const bytes = Uint8Array.from(atob(response.body), char => char.charCodeAt(0));
        const headers = {'Content-Type': response.content_type};
        if (response.filename) headers['Content-Disposition'] = 'attachment; filename="' + response.filename.replace(/["\r\n]/g, '') + '"';
        item.resolve(new Response(bytes, {status: response.status, headers}));
      } catch (error) { item.reject(error); }
    }
    frameHeight();
    pump();
  });
  const artifactPath = value => value.includes(imageMarker) ? decodeURIComponent(value.split(imageMarker)[1]) : null;
  function loadImage(path) {
    if (!images.has(path)) images.set(path, rpc('/api/artifact?path=' + encodeURIComponent(path))
      .then(async response => {
        if (!response.ok) throw new Error((await response.json()).error || 'Preview unavailable.');
        return URL.createObjectURL(await response.blob());
      }).catch(error => { images.delete(path); throw error; }));
    return images.get(path);
  }
  function hydrateImages() {
    document.querySelectorAll('img[src*="#wqc-artifact="]').forEach(img => {
      if (img.dataset.wqcLoading) return;
      const original = img.getAttribute('src');
      img.dataset.wqcLoading = 'true';
      loadImage(artifactPath(original)).then(url => {
        if (img.isConnected && img.getAttribute('src') === original) img.src = url;
      }).catch(error => {
        if (img.isConnected) {
          const note = document.createElement('p');
          note.className = 'small-note';
          note.textContent = error.message;
          img.replaceWith(note);
        }
      });
    });
  }
  document.addEventListener('click', event => {
    const anchor = event.target.closest('a[download]');
    if (!anchor) return;
    const path = artifactPath(anchor.getAttribute('href') || '');
    if (!path) return;
    event.preventDefault();
    loadImage(path).then(url => {
      const link = document.createElement('a');
      link.href = url;
      link.download = path.split(/[\\/]/).pop() || 'website-preview.png';
      link.click();
    }).catch(error => {
      const region = document.querySelector('#toasts');
      const message = document.createElement('div');
      message.className = 'toast';
      message.textContent = error.message;
      if (region) region.replaceChildren(message);
    });
  }, true);
  window.WQCStreamlit = {artifact: path => placeholder + imageMarker + encodeURIComponent(path)};
  const observer = new MutationObserver(hydrateImages);
  observer.observe(document.documentElement, {childList: true, subtree: true, attributes: true, attributeFilter: ['src']});
  window.addEventListener('resize', frameHeight);
  try { window.parent.addEventListener('resize', frameHeight); } catch (_) {}
  window.addEventListener('beforeunload', () => {
    observer.disconnect();
    try { window.parent.removeEventListener('resize', frameHeight); } catch (_) {}
    images.forEach(promise => promise.then(URL.revokeObjectURL, () => {}));
  });
  send('streamlit:componentReady', {apiVersion: 1});
  frameHeight();
})();
