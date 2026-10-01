// Heartbeat & Auto-Shutdown on Browser Close
    function sendHeartbeat() {
      fetch('/api/heartbeat', { method: 'POST' }).catch(() => {});
    }
    sendHeartbeat();
    setInterval(sendHeartbeat, 2500);

    function notifyClose() {
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/shutdown');
      } else {
        fetch('/api/shutdown', { method: 'POST', keepalive: true }).catch(() => {});
      }
    }

    window.addEventListener('pagehide', notifyClose);
    window.addEventListener('beforeunload', notifyClose);

    // Startup
    setupMarked();
    loadFiles();
