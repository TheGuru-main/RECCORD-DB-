const API_BASE = "";

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
    throw new Error("Network error: cannot reach API");
  }
  const data = await res.json().catch(function () { return {}; });
  if (!res.ok) {
    const message = data.detail || data.message || ("HTTP " + res.status);
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

const AuthAPI = {
  regularSignup(p) {
    return api("/auth/regular/signup", { method: "POST", body: p });
  },
  regularLogin(p) {
    return api("/auth/regular/login", { method: "POST", body: p });
  },
  organisationSignup(p) {
    return api("/auth/organisation/signup", { method: "POST", body: p });
  },
  organisationLogin(p) {
    return api("/auth/organisation/login", { method: "POST", body: p });
  },
  workerRoles(p) {
    return api("/auth/worker/roles", { method: "POST", body: p });
  },
  workerRegister(p) {
    return api("/auth/worker/register", { method: "POST", body: p });
  },
  workerLogin(p) {
    return api("/auth/worker/login", { method: "POST", body: p });
  },

  async loginAny(identifier, password) {
    const id = (identifier || "").trim();
    const pw = password || "";
    if (!id || !pw) throw new Error("Enter your credentials");

    const attempts = [
      function () { return AuthAPI.regularLogin({ phone: id, password: pw }); },
      function () { return AuthAPI.organisationLogin({ phone: id, password: pw }); },
      function () { return AuthAPI.workerLogin({ worker_phone: id, worker_password: pw }); },
      function () { return AuthAPI.regularLogin({ username: id, password: pw }); }
    ];

    var lastErr = "Invalid credentials";
    for (var i = 0; i < attempts.length; i++) {
      try {
        return await attempts[i]();
      } catch (e) {
        lastErr = e.message || lastErr;
      }
    }
    throw new Error(lastErr);
  }
};

const ObjectsAPI = {
  create(name, description) {
    var body = { name: name };
    if (description) body.description = description;
    return api("/objects", { method: "POST", body: body });
  },
  get(id) {
    return api("/objects/" + id);
  }
};

const NarrationsAPI = {
  create(objectId, content) {
    return api("/narrations", {
      method: "POST",
      body: { object_id: objectId, content: content }
    });
  },
  byObject(objectId) {
    return api("/narrations/by-object/" + objectId);
  }
};

const MediaAPI = {
  upload(objectId, filename, contentType, dataBase64) {
    return api("/media/upload", {
      method: "POST",
      body: {
        object_id: objectId,
        filename: filename,
        content_type: contentType,
        data_base64: dataBase64
      }
    });
  },
  list(objectId) {
    return api("/media/object/" + objectId);
  }
};

const GridAPI = {
  getMine() {
    return api("/grid");
  }
};

const ElectionsAPI = {
  create(p) {
    return api("/elections/create", { method: "POST", body: p });
  },
  addCandidate(p) {
    return api("/elections/candidates", { method: "POST", body: p });
  },
  publish(id) {
    return api("/elections/" + id + "/publish", { method: "POST" });
  },
  getByCredential(c) {
    return api("/elections/credential/" + encodeURIComponent(c));
  },
  listCandidates(id) {
    return api("/elections/" + id + "/candidates");
  },
  registerVoter(p) {
    return api("/elections/voters/register", { method: "POST", body: p });
  },
  castVote(p) {
    return api("/elections/vote", { method: "POST", body: p });
  },
  getResults(id) {
    return api("/elections/" + id + "/results");
  },
  listHostElections(phone) {
    return api("/elections/host/" + encodeURIComponent(phone));
  },
  listVoters(electionId) {
    return api("/elections/" + electionId + "/voters");
  },
  getVoter(voterId) {
    return api("/elections/voters/" + voterId);
  }
};

function saveSession(data) {
  localStorage.setItem("reccord_token", data.access_token || "");
  localStorage.setItem("reccord_account_type", data.account_type || "");
  if (data.user) localStorage.setItem("reccord_user", JSON.stringify(data.user));
  if (data.organisation) {
    localStorage.setItem("reccord_organisation", JSON.stringify(data.organisation));
  }
  if (data.worker) localStorage.setItem("reccord_worker", JSON.stringify(data.worker));
  if (data.worker_credential) {
    localStorage.setItem("reccord_worker_credential", data.worker_credential);
  }
}

function clearSession() {
  [
    "reccord_token",
    "reccord_account_type",
    "reccord_user",
    "reccord_organisation",
    "reccord_worker",
    "reccord_worker_credential"
  ].forEach(function (k) {
    localStorage.removeItem(k);
  });
}
