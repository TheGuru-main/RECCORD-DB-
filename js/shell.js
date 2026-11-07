function openDrawer() {
  document.getElementById("sideDrawer") && document.getElementById("sideDrawer").classList.add("open");
  document.getElementById("drawerOverlay") && document.getElementById("drawerOverlay").classList.add("show");
}
function closeDrawer() {
  document.getElementById("sideDrawer") && document.getElementById("sideDrawer").classList.remove("open");
  document.getElementById("drawerOverlay") && document.getElementById("drawerOverlay").classList.remove("show");
}
function requireAuth() {
  if (!localStorage.getItem("reccord_token")) {
    window.location.href = "/pages/login.html";
    return false;
  }
  return true;
}
function getDisplayName() {
  const t = localStorage.getItem("reccord_account_type") || "";
  const u = JSON.parse(localStorage.getItem("reccord_user") || "null");
  const o = JSON.parse(localStorage.getItem("reccord_organisation") || "null");
  if (t === "organisation" && o) return o.display_name || o.business_name || "Organisation";
  if (u) return u.name || u.username || "User";
  return "User";
}
function logout() {
  if (typeof clearSession === "function") clearSession();
  else localStorage.clear();
  window.location.href = "/pages/landing.html";
}
