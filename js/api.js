// RECCORD DB API helper
// Replace with your real Render URL after first deploy
const API_BASE = "https://reccord-api.onrender.com";

async function api(path, options = {}) {
  const url = API_BASE + path;
  const config = {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  };

  if (config.body && typeof config.body === "object") {
    config.body = JSON.stringify(config.body);
  }

  const res = await fetch(url, config);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = data.detail || data.message || "Request failed";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

const ElectionsAPI = {
  create(payload) {
    return api("/elections/create", { method: "POST", body: payload });
  },
  addCandidate(payload) {
    return api("/elections/candidates", { method: "POST", body: payload });
  },
  publish(electionId) {
    return api(`/elections/${electionId}/publish`, { method: "POST" });
  },
  getByCredential(credential) {
    return api(`/elections/credential/${credential}`);
  },
  listCandidates(electionId) {
    return api(`/elections/${electionId}/candidates`);
  },
  registerVoter(payload) {
    return api("/elections/voters/register", { method: "POST", body: payload });
  },
  castVote(payload) {
    return api("/elections/vote", { method: "POST", body: payload });
  },
  getResults(electionId) {
    return api(`/elections/${electionId}/results`);
  },
  listHostElections(hostPhone) {
    return api(`/elections/host/${hostPhone}`);
  }
};
