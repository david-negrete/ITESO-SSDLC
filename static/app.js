const byId = (id) => document.getElementById(id);
let current = null;
function message(text, error = false) { byId('status').textContent = text; byId('status').className = error ? 'error' : 'success'; }
async function api(path, method = 'GET', body) {
  const headers = {};
  if (method !== 'GET') {
    const csrf = await fetch('/api/csrf').then(r => r.json());
    headers['X-CSRF-Token'] = csrf.token;
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(path, { method, headers, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  const data = await response.json();
  if (!response.ok) throw new Error(`${response.status}: ${data.error || 'Request failed.'}`);
  return data;
}
function showSession(user) {
  current = user;
  byId('login-panel').hidden = !!user;
  byId('profile-panel').hidden = !user;
  byId('profile').hidden = true;
  if (user) { byId('identity').textContent = `Signed in as profile ${user.id} (${user.role}).`; byId('profile-id').value = user.id; }
}
async function loadProfile() {
  byId('profile').hidden = true;
  try {
    const profile = await api(`/api/profiles/${byId('profile-id').value}`);
    byId('name').textContent = profile.name;
    byId('team').textContent = profile.team;
    byId('bio').value = profile.bio;
    byId('profile').hidden = false;
    message('200: Profile loaded.');
  } catch (error) { message(error.message, true); }
}
byId('login-form').addEventListener('submit', async event => {
  event.preventDefault();
  try { showSession(await api('/api/login', 'POST', { username: byId('username').value, password: byId('password').value })); byId('password').value = ''; await loadProfile(); }
  catch (error) { message(error.message, true); }
});
byId('logout').addEventListener('click', async () => { try { await api('/api/logout', 'POST', {}); showSession(null); byId('bio').value = ''; message('Signed out.'); } catch (error) { message(error.message, true); } });
byId('load').addEventListener('click', loadProfile);
byId('profile-id').addEventListener('change', () => { byId('profile').hidden = true; });
byId('save').addEventListener('click', async () => { try { await api(`/api/profiles/${byId('profile-id').value}`, 'PATCH', { bio: byId('bio').value }); message('200: Bio saved.'); } catch (error) { message(error.message, true); } });
api('/api/me').then(showSession).catch(() => showSession(null));
