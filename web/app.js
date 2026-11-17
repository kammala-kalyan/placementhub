// PlacementHub web UI: plain JavaScript, no framework or build step.
// All API calls go to /api/... which nginx forwards to the FastAPI service.
// Text from messages is inserted with textContent (never innerHTML), so a
// malicious message cannot inject HTML or scripts into the page.

const API = "/api";
const DAY_MS = 24 * 60 * 60 * 1000;

const form = document.getElementById("search-form");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const template = document.getElementById("card-template");

// ---------- dates ----------

function todayLocal() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

function isoDate(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function parseIsoDate(text) {
  const [y, m, d] = text.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

// Returns { cls, label } used for the coloured deadline highlight.
function deadlineInfo(deadlineText) {
  if (!deadlineText) return { cls: "", label: "No deadline" };
  const deadline = parseIsoDate(deadlineText);
  const days = Math.round((deadline - todayLocal()) / DAY_MS);
  const date = deadline.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
  if (days < 0) return { cls: "closed", label: `Closed ${date}` };
  if (days === 0) return { cls: "urgent", label: "Closes today" };
  if (days === 1) return { cls: "urgent", label: "Closes tomorrow" };
  if (days <= 3) return { cls: "soon", label: `${days} days left` };
  return { cls: "", label: `Apply by ${date}` };
}

// ---------- rendering ----------

function addFact(list, text, className) {
  const li = document.createElement("li");
  li.textContent = text;
  if (className) li.className = className;
  list.appendChild(li);
}

function renderCard(job) {
  const card = template.content.firstElementChild.cloneNode(true);
  const info = deadlineInfo(job.deadline);
  if (info.cls) card.classList.add(info.cls);

  card.querySelector(".category").textContent = job.category || "Other";
  card.querySelector(".deadline").textContent = info.label;
  card.querySelector(".company").textContent = job.company || "Unknown company";
  card.querySelector(".role").textContent = job.role || "";

  const facts = card.querySelector(".facts");
  if (job.ctc_lpa) addFact(facts, `💰 ₹${job.ctc_lpa} LPA`);
  else if (job.stipend_month) addFact(facts, `💰 ₹${job.stipend_month.toLocaleString("en-IN")}/month stipend`);
  if (job.location) addFact(facts, `📍 ${job.location}`);
  const eligibility = [];
  if (job.branches && job.branches.length) eligibility.push(job.branches.join(", "));
  if (job.cgpa_min) eligibility.push(`CGPA ≥ ${job.cgpa_min}`);
  if (job.batch && job.batch.length) eligibility.push(`${job.batch.join(", ")} batch`);
  if (eligibility.length) addFact(facts, `🎓 ${eligibility.join(" · ")}`);

  // Resume Match fields (present only on /jobs/match results).
  if (typeof job.match_score === "number") {
    addFact(facts, `✅ ${job.match_score}% skills match`, "match");
    if (job.missing_skills && job.missing_skills.length) {
      addFact(facts, `Missing: ${job.missing_skills.join(", ")}`, "missing");
    }
  }

  const apply = card.querySelector(".apply");
  if (job.apply_link && /^https?:\/\//i.test(job.apply_link)) {
    apply.href = job.apply_link;
  } else {
    apply.remove();
  }
  return card;
}

function renderResults(data, emptyText) {
  resultsEl.replaceChildren(...data.items.map(renderCard));
  if (!data.items.length) {
    statusEl.textContent = emptyText;
    return;
  }
  statusEl.textContent = `${data.total} opening${data.total === 1 ? "" : "s"} found`;
  if (data.cached) {
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = "served from cache";
    statusEl.appendChild(badge);
  }
}

// ---------- search ----------

function currentParams() {
  const params = new URLSearchParams();
  for (const name of ["q", "category", "role", "location", "sort"]) {
    const value = form.elements[name].value.trim();
    if (value) params.set(name, value);
  }
  if (form.elements.closing.checked) {
    const today = todayLocal();
    params.set("deadline_from", isoDate(today));
    params.set("deadline_to", isoDate(new Date(today.getTime() + 3 * DAY_MS)));
  }
  params.set("size", "30");
  return params;
}

let requestId = 0;

async function search() {
  const params = currentParams();
  const myRequest = ++requestId;   // ignore answers to older, slower requests
  statusEl.textContent = "Searching…";
  // Keep the URL shareable: copy it and the same search opens again.
  const shareable = new URLSearchParams(params);
  shareable.delete("size");
  history.replaceState(null, "", shareable.toString() ? `?${shareable}` : location.pathname);
  try {
    const resp = await fetch(`${API}/jobs/search?${params}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (myRequest === requestId) renderResults(data, "No openings match these filters.");
  } catch (err) {
    if (myRequest === requestId) {
      resultsEl.replaceChildren();
      statusEl.textContent = "Search is unavailable right now. Please try again shortly.";
    }
  }
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

const searchSoon = debounce(search, 300);
form.addEventListener("input", searchSoon);
form.addEventListener("change", searchSoon);
form.addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});

// ---------- Resume Match ----------

const resumeForm = document.getElementById("resume-form");
const resumeResult = document.getElementById("resume-result");
const clearMatch = document.getElementById("clear-match");

function listOf(items, className) {
  const list = document.createElement("ul");
  list.className = className;
  for (const text of items) {
    const li = document.createElement("li");
    li.textContent = text;
    list.appendChild(li);
  }
  return list;
}

function showResumeSummary(resume) {
  const heading = document.createElement("p");
  heading.textContent = resume.skills.length
    ? `Skills found in your resume (${resume.skills.length}):`
    : "No known skills were found in your resume.";
  const parts = [heading, listOf(resume.skills, "chips")];
  if (resume.suggestions.length) {
    const tipsTitle = document.createElement("p");
    tipsTitle.textContent = "Wording tips (for skills you already listed):";
    parts.push(tipsTitle, listOf(resume.suggestions, "tips"));
  }
  resumeResult.replaceChildren(...parts);
}

async function matchResume(event) {
  event.preventDefault();
  const button = resumeForm.querySelector("button[type=submit]");
  const file = document.getElementById("resume-file").files[0];
  if (!file) return;
  button.disabled = true;
  statusEl.textContent = "Reading your resume…";
  try {
    const body = new FormData();
    body.append("file", file);
    const upload = await fetch(`${API}/resume`, { method: "POST", body });
    const resume = await upload.json();
    if (!upload.ok) throw new Error(resume.detail || `HTTP ${upload.status}`);
    showResumeSummary(resume);

    const params = new URLSearchParams({
      resume_id: resume.resume_id,
      skills: resume.skills.join(","),      // fallback if the server forgot the resume
      min_score: document.getElementById("min-score").value,
    });
    const resp = await fetch(`${API}/jobs/match?${params}`);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
    requestId++;                              // ignore any search still in flight
    renderResults(data, `No openings match at least ${data.min_score}% of their skills yet.`);
    if (data.items.length) statusEl.textContent = `${data.total} openings match ≥ ${data.min_score}% of their skills`;
    clearMatch.hidden = false;
  } catch (err) {
    statusEl.textContent = `Resume match failed: ${err.message}`;
  } finally {
    button.disabled = false;
  }
}

resumeForm.addEventListener("submit", matchResume);
clearMatch.addEventListener("click", () => {
  clearMatch.hidden = true;
  resumeResult.replaceChildren();
  search();
});

// ---------- health indicator ----------

async function checkHealth() {
  const el = document.getElementById("health");
  const text = document.getElementById("health-text");
  try {
    const resp = await fetch(`${API}/health`);
    const data = await resp.json();
    el.className = `health ${data.status}`;
    text.textContent = data.status === "ok" ? "all systems up"
      : data.status === "degraded" ? "degraded (cache off)" : "search down";
  } catch {
    el.className = "health down";
    text.textContent = "API unreachable";
  }
}

// ---------- start ----------

function restoreFromUrl() {
  const params = new URLSearchParams(location.search);
  for (const name of ["q", "category", "role", "location", "sort"]) {
    if (params.has(name)) form.elements[name].value = params.get(name);
  }
}

restoreFromUrl();
search();
checkHealth();
setInterval(checkHealth, 30000);
