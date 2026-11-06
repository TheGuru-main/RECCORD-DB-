const API_BASE = "https://reccord-db-apiv1-0-0-1q.onrender.com";

async function api(path, options = {}) {
  const url = API_BASE + path;
  const token = localStorage.getItem("reccord_token");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (token && !headers.Authorization) {
    headers.Authorization = "Bearer " + token;
  }
  const config = { ...options, headers };
  if (config.body && typeof config.body === "object") {
    config.body = JSON.stringify(config.body);
  }

  let res;
  try {
    res = await fetch(url, config);
  } catch (err) {
    throw new Error("Network error: cannot reach API (" + API_BASE + ")");
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || data.message || ("HTTP " + res.status);
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

const AuthAPI = {
  regularSignup(p) { return api("/auth/regular/signup", { method: "POST", body: p }); },
  regularLogin(p) { return api("/auth/regular/login", { method: "POST", body: p }); },
  organisationSignup(p) { return api("/auth/organisation/signup", { method: "POST", body: p }); },
  organisationLogin(p) { return api("/auth/organisation/login", { method: "POST", body: p }); },
  workerRoles(p) { return api("/auth/worker/roles", { method: "POST", body: p }); },
  workerRegister(p) { return api("/auth/worker/register", { method: "POST", body: p }); },
  workerLogin(p) { return api("/auth/worker/login", { method: "POST", body: p }); }
};

const ObjectsAPI = {
  create(name) { return api("/objects", { method: "POST", body: { name } }); },
  get(id) { return api("/objects/" + id); }
};

const NarrationsAPI = {
  create(objectId, content) {
    return api("/narrations", {
      method: "POST",
      body: { object_id: objectId, content }
    });
  }
};

const GridAPI = {
  getMine() { return api("/grid"); }
};

const ElectionsAPI = {
  create(p) { return api("/elections/create", { method: "POST", body: p }); },
  addCandidate(p) { return api("/elections/candidates", { method: "POST", body: p }); },
  publish(id) { return api("/elections/" + id + "/publish", { method: "POST" }); },
  getByCredential(c) { return api("/elections/credential/" + c); },
  listCandidates(id) { return api("/elections/" + id + "/candidates"); },
  registerVoter(p) { return api("/elections/voters/register", { method: "POST", body: p }); },
  castVote(p) { return api("/elections/vote", { method: "POST", body: p }); },
  getResults(id) { return api("/elections/" + id + "/results"); },
  listHostElections(phone) { return api("/elections/host/" + phone); }
};

function saveSession(data) {
  localStorage.setItem("reccord_token", data.access_token || "");
  localStorage.setItem("reccord_account_type", data.account_type || "");
  if (data.user) localStorage.setItem("reccord_user", JSON.stringify(data.user));
  if (data.organisation) localStorage.setItem("reccord_organisation", JSON.stringify(data.organisation));
  if (data.worker) localStorage.setItem("reccord_worker", JSON.stringify(data.worker));
  if (data.worker_credential) localStorage.setItem("reccord_worker_credential", data.worker_credential);
}

function clearSession() {
  [
    "reccord_token",
    "reccord_account_type",
    "reccord_user",
    "reccord_organisation",
    "reccord_worker",
    "reccord_worker_credential"
  ].forEach(function (k) { localStorage.removeItem(k); });
}
