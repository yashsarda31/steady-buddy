let installPrompt = null;
const install = document.querySelector('#install');
const dialog = document.querySelector('#install-help');
const connection = document.querySelector('#connection');
const lock = document.querySelector('#lock');
const standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone;
if (standalone) install.hidden = true;
if ('serviceWorker' in navigator && window.isSecureContext) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}
addEventListener('beforeinstallprompt', event => {
  event.preventDefault(); installPrompt = event; install.hidden = false;
});
addEventListener('appinstalled', () => { install.hidden = true; installPrompt = null; });
install.addEventListener('click', async () => {
  if (installPrompt) {
    const prompt = installPrompt; installPrompt = null;
    await prompt.prompt(); await prompt.userChoice;
  } else {
    document.querySelector('#install-status').textContent = window.isSecureContext
      ? 'Your browser may offer installation in its menu. Use the main app address for installation.'
      : 'Open this app at an HTTPS address to install it on your phone. A plain local network address is not enough.';
    dialog.showModal();
  }
});
document.querySelector('#close-help').addEventListener('click', () => dialog.close());
fetch('/session', {cache: 'no-store'}).then(r => r.ok ? r.json() : null).then(data => {
  if (data?.password_enabled) lock.hidden = false;
}).catch(() => {});
lock.addEventListener('click', async () => {
  const response = await fetch('/lock', {method: 'POST'});
  if (response.ok) {
    // Stop the active iframe connection as soon as the user locks the app.
    document.querySelector('#buddy-frame').src = 'about:blank';
    location.replace('/login');
  }
});
let disconnected = false;
async function checkConnection() {
  if (document.hidden) return;
  try {
    const response = await fetch('/health', {cache: 'no-store', signal: AbortSignal.timeout(4000)});
    if (!response.ok) throw new Error('Unavailable');
    connection.hidden = true;
    if (disconnected) document.querySelector('#buddy-frame').src = '/streamlit/?embed=true';
    disconnected = false;
  } catch {
    disconnected = true; connection.hidden = false;
  }
}
addEventListener('offline', () => { disconnected = true; connection.hidden = false; });
addEventListener('online', checkConnection);
document.addEventListener('visibilitychange', () => { if (!document.hidden) checkConnection(); });
setInterval(checkConnection, 15000);
