function openDrawer() {
  document.getElementById('sideDrawer')?.classList.add('open');
  document.getElementById('drawerOverlay')?.classList.add('show');
}
function closeDrawer() {
  document.getElementById('sideDrawer')?.classList.remove('open');
  document.getElementById('drawerOverlay')?.classList.remove('show');
}

function requireAuth() {
  const token = localStorage.getItem('reccord_token');
  if (!token) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

function getDisplayName() {
  const accountType = localStorage.getItem('reccord_account_type') || '';
  const user = JSON.parse(localStorage.getItem('reccord_user') || 'null');
  const org = JSON.parse(localStorage.getItem('reccord_organisation') || 'null');
  if (accountType === 'organisation' && org) {
    return org.display_name || org.business_name || 'Organisation';
  }
  if (user) return user.name || user.username || 'User';
  return 'User';
}

function isAdmin() {
  return localStorage.getItem('reccord_account_type') === 'organisation';
}

function logout() {
  if (typeof clearSession === 'function') clearSession();
  else {
    ['reccord_token','reccord_account_type','reccord_user','reccord_organisation','reccord_worker_credential']
      .forEach(k => localStorage.removeItem(k));
  }
  window.location.href = '../index.html';
}
