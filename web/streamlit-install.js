export default function ({parentElement, data, setStateValue}) {
  const button = parentElement.querySelector('#install');
  const help = parentElement.querySelector('#help');
  const storage = parentElement.querySelector('#storage');
  // Community Cloud puts the running app inside a same-origin /~/+/ iframe.
  // Install metadata belongs to the outer document users actually bookmark.
  let host = window;
  try { if (window.parent.location.origin === location.origin) host = window.parent; } catch {}
  const wrapped = host.document.querySelector('#buddy-frame');
  if (wrapped) button.hidden = true;
  else {
    const cloudPrefix = location.pathname.includes('/~/+/') ? '/~/+/' : '/';
    const base = new URL(cloudPrefix + 'app/static/', location.origin);
    let link = host.document.querySelector('link[rel="manifest"]');
    if (!link) { link = host.document.createElement('link'); link.rel = 'manifest'; host.document.head.append(link); }
    const manifest = new URL('manifest.json', base).href;
    link.crossOrigin = 'use-credentials';
    if (link.href !== manifest) link.href = manifest;
    for (const [rel, file] of [['apple-touch-icon', 'apple-touch-icon.png'], ['icon', 'icon-192.png']]) {
      let icon = host.document.querySelector(`link[rel="${rel}"]`);
      if (!icon) { icon = host.document.createElement('link'); icon.rel = rel; host.document.head.append(icon); }
      icon.href = new URL('icons/' + file, base).href;
    }
    for (const [name, content] of [['theme-color', '#284C38'], ['apple-mobile-web-app-capable', 'yes']]) {
      let meta = host.document.querySelector(`meta[name="${name}"]`);
      if (!meta) { meta = host.document.createElement('meta'); meta.name = name; host.document.head.append(meta); }
      meta.content = content;
    }
  }
  const installed = () => host.matchMedia('(display-mode: standalone)').matches || host.navigator.standalone;
  if (installed() || host.__steadyInstall?.installed) button.hidden = true;
  // Retain the browser prompt across Streamlit page changes and component mounts.
  if (!host.__steadyInstall) {
    host.__steadyInstall = {prompt: null, installed: false};
    host.addEventListener('beforeinstallprompt', event => {
      event.preventDefault(); host.__steadyInstall.prompt = event;
    });
    host.addEventListener('appinstalled', () => {
      host.__steadyInstall.prompt = null; host.__steadyInstall.installed = true;
    });
  }
  const onInstalled = () => { button.hidden = true; help.hidden = true; };
  host.addEventListener('appinstalled', onInstalled);
  button.onclick = async () => {
    const prompt = host.__steadyInstall.prompt;
    if (prompt) {
      host.__steadyInstall.prompt = null;
      try { await prompt.prompt(); await prompt.userChoice; return; } catch {}
    }
    parentElement.querySelector('#secure').textContent = host.isSecureContext
      ? 'If your browser does not offer installation, you can still add a home-screen shortcut.'
      : 'Open the app at an HTTPS address to install it on your phone.';
    help.hidden = false;
    parentElement.querySelector('#close').focus();
  };
  parentElement.querySelector('#close').onclick = () => { help.hidden = true; button.focus(); };
  if (data.cloud) storage.textContent = 'Your diary belongs to this browser. Keep a downloaded backup for another device.';
  if (data.cloud && !data.identity_ready) {
    try {
      let record = JSON.parse(localStorage.getItem('steady-buddy-diary-v1') || 'null');
      if (!record) {
        const token = Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, '0')).join('');
        record = {token, backup: null};
        localStorage.setItem('steady-buddy-diary-v1', JSON.stringify(record));
      }
      if (!/^[a-f0-9]{64}$/.test(record.token)) throw new Error('Invalid identity');
      // Send once per Streamlit session so background backup updates cannot interrupt inputs.
      setStateValue('identity', record);
      storage.textContent = 'Your diary belongs to this browser. Keep a downloaded backup for another device.';
    } catch {
      storage.textContent = 'Allow site storage to open your personal diary. Private browsing may not keep a recovery copy.';
      setStateValue('identity', {error: 'storage'});
    }
  }
  return () => { host.removeEventListener('appinstalled', onInstalled); button.onclick = null; };
}
