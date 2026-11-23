/* CMC Hybrid Briefs — web app.
 *
 * ALL AI inference in this app goes through Firebase AI Logic. No other
 * model API is called from anywhere in this project.
 *
 * Hybrid routing (decided server-side in cmc_agent/hybrid.py, applied here):
 * - Quick verdict  -> InferenceMode.PREFER_ON_DEVICE (Gemini Nano 4 on
 *   Chrome when available, cloud fallback). Single-turn text generation.
 * - Deep brief     -> InferenceMode.PREFER_IN_CLOUD (cloud Gemini model).
 * - "Keep on-device" checked -> InferenceMode.ONLY_ON_DEVICE.
 *
 * Per the Firebase AI Logic docs, getGenerativeModel() is called on the
 * user's Ask click (on / after a user interaction), which is a
 * prerequisite for the inferenceMode option. The response's
 * inferenceSource ("ON_DEVICE" / "IN_CLOUD", JS SDK v12.5.0+) is shown
 * next to the verdict so the user can see where the answer ran.
 *
 * Without firebase-config.js the page still works: it shows the live
 * brief, the routing decision and the exact grounded prompt, and says
 * plainly that the AI verdict needs Firebase. It never fakes an answer.
 */

const SDK_VERSION = "12.5.0";
const SDK_BASE = `https://www.gstatic.com/firebasejs/${SDK_VERSION}`;

const statusEl = document.getElementById("firebase-status");
const askBtn = document.getElementById("ask-btn");
const questionEl = document.getElementById("question");

let firebase = null; // { app, ai } once initialised, else null

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = "status" + (kind ? " " + kind : "");
}

async function loadConfig() {
  try {
    const mod = await import("./firebase-config.js");
    const cfg = mod.firebaseConfig || {};
    if (!cfg.apiKey || cfg.apiKey === "YOUR_API_KEY") return null;
    return cfg;
  } catch {
    return null; // no firebase-config.js yet — routing-preview mode
  }
}

async function initFirebase(cfg) {
  const { initializeApp } = await import(`${SDK_BASE}/firebase-app.js`);
  const { getAI, GoogleAIBackend } = await import(`${SDK_BASE}/firebase-ai.js`);
  if (cfg.appCheckDebugToken) {
    // Local development only: App Check debug token.
    self.FIREBASE_APPCHECK_DEBUG_TOKEN = true;
  }
  const app = initializeApp(cfg);
  if (cfg.recaptchaSiteKey) {
    const { initializeAppCheck, ReCaptchaV3Provider } = await import(
      `${SDK_BASE}/firebase-app-check.js`
    );
    initializeAppCheck(app, {
      provider: new ReCaptchaV3Provider(cfg.recaptchaSiteKey),
      isTokenAutoRefreshEnabled: true,
    });
  }
  // Gemini Developer API backend for the cloud leg of hybrid inference.
  const ai = getAI(app, { backend: new GoogleAIBackend() });
  return { app, ai, cfg };
}

// Heuristic grounding guard (mirrors cmc_agent/hybrid.py): flag any
// $- or %-number in the model output that does not appear in the brief.
function groundingFlags(aiText, briefText) {
  const re = /\$[\d,]+(?:\.\d+)?|\b\d+(?:\.\d+)?%/g;
  const norm = (s) => s.replace(/[$,%]/g, "");
  const inBrief = new Set((briefText.match(re) || []).map(norm));
  return (aiText.match(re) || []).map(norm).filter((n) => !inBrief.has(n));
}

async function runAiVerdict(feature, isPrivate, prompt, briefText, cloudModel) {
  // Called from the Ask click handler: getGenerativeModel() must be
  // created on / after a user interaction for inferenceMode to apply.
  const { getGenerativeModel, InferenceMode } = await import(
    `${SDK_BASE}/firebase-ai.js`
  );
  let mode = InferenceMode.PREFER_ON_DEVICE;
  // inCloudParams must be set for PREFER_ON_DEVICE too: when Gemini Nano
  // is unavailable the SDK falls back to the cloud, and without an
  // explicit cloud model it uses its own default (gemini-2.0-flash-lite),
  // which Google has discontinued (404). Only ONLY_ON_DEVICE omits it.
  let modelOptions = { mode, inCloudParams: { model: cloudModel } };
  if (isPrivate) {
    mode = InferenceMode.ONLY_ON_DEVICE;
    modelOptions = { mode };
  } else if (feature === "deep_brief") {
    mode = InferenceMode.PREFER_IN_CLOUD;
    modelOptions = { mode, inCloudParams: { model: cloudModel } };
  }
  const model = getGenerativeModel(firebase.ai, modelOptions);
  const result = await model.generateContent(prompt);
  const text = result.response.text();
  // "ON_DEVICE" or "IN_CLOUD" (JS SDK v12.5.0+).
  const source = result.response.inferenceSource || "unknown";
  return { text, source, mode };
}

async function ask() {
  const question = questionEl.value.trim();
  if (!question) {
    questionEl.focus();
    return;
  }
  const feature = document.querySelector('input[name="feature"]:checked').value;
  const isPrivate = document.getElementById("private").checked;
  askBtn.disabled = true;
  askBtn.textContent = "Working…";
  try {
    const briefRes = await fetch(`/api/ask?q=${encodeURIComponent(question)}`);
    if (!briefRes.ok) throw new Error(`Brief request failed (HTTP ${briefRes.status})`);
    const briefData = await briefRes.json();
    if (briefData.error) throw new Error(briefData.error);
    document.getElementById("brief").textContent = briefData.brief;
    document.getElementById("evidence").textContent =
      (briefData.mock ? "[mock] Labeled mock data — no live CMC call.\n" : "") +
      briefData.evidence.join("\n");
    document.getElementById("brief-section").hidden = false;

    const symbolMatch = question.match(/\b(btc|eth|sol|xrp|bnb|doge)\b/i);
    const symbol = symbolMatch ? symbolMatch[1].toUpperCase() : "BTC";
    const prevRes = await fetch(
      `/api/hybrid-preview?symbol=${symbol}&feature=${feature}&private=${isPrivate ? 1 : 0}`
    );
    const preview = await prevRes.json();
    if (preview.error) throw new Error(preview.error);
    document.getElementById("routing").textContent =
      `Feature: ${preview.feature} | Firebase AI Logic mode: ${preview.mode} | ` +
      `Cloud model: ${preview.cloud_model} | Data: ${preview.mock ? "mock" : "live CMC"}`;
    document.getElementById("prompt").textContent = preview.prompt;

    const aiSection = document.getElementById("ai-section");
    aiSection.hidden = false;
    if (!firebase) {
      document.getElementById("noconfig").hidden = false;
      document.getElementById("ai-text").textContent =
        "AI verdict unavailable — Firebase is not configured. " +
        "The routing decision and the exact prompt are shown below; that is " +
        "everything this app would send to Firebase AI Logic.";
      document.getElementById("source-badge").textContent = "not run";
      document.getElementById("grounding-note").textContent = "";
      return;
    }
    document.getElementById("noconfig").hidden = true;
    const { text, source } = await runAiVerdict(
      feature, isPrivate, preview.prompt, briefData.brief, firebase.cfg.cloudModel || "gemini-3.5-flash-lite"
    );
    document.getElementById("ai-text").textContent = text;
    const badge = document.getElementById("source-badge");
    badge.textContent = source === "ON_DEVICE" ? "ran on-device" : source === "IN_CLOUD" ? "ran in cloud" : source;
    badge.className = "badge " + (source === "ON_DEVICE" ? "on-device" : source === "IN_CLOUD" ? "in-cloud" : "");
    const flags = groundingFlags(text, briefData.brief);
    document.getElementById("grounding-note").textContent = flags.length
      ? `Grounding flag: these numbers are not in the brief, treat them with care: ${[...new Set(flags)].join(", ")}`
      : "Grounding check: every number in this verdict also appears in the brief.";
  } catch (err) {
    setStatus(`Error: ${err.message}. Is the local server running? Start it with: python -m cmc_agent.server`, "warn");
  } finally {
    askBtn.disabled = false;
    askBtn.textContent = "Ask";
  }
}

document.querySelectorAll(".chips button").forEach((btn) => {
  btn.addEventListener("click", () => {
    questionEl.value = btn.dataset.q;
    ask();
  });
});
askBtn.addEventListener("click", ask);
questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") ask();
});

// Deep link: ?q=<question> fills the box and asks on load (demo + screenshots).
const deepQ = new URLSearchParams(location.search).get("q");
if (deepQ) {
  questionEl.value = deepQ;
  ask();
}

// Startup: Firebase is optional for viewing data; required for AI verdicts.
loadConfig()
  .then((cfg) => {
    if (!cfg) {
      setStatus("Firebase not configured — data + routing preview work; AI verdict needs firebase-config.js (see README).", "warn");
      return null;
    }
    return initFirebase(cfg);
  })
  .then((fb) => {
    if (fb) {
      firebase = fb;
      setStatus("Firebase AI Logic ready — on-device (Gemini Nano 4) + cloud (Gemini). App Check: " +
        (fb.cfg.recaptchaSiteKey ? "reCAPTCHA v3" : fb.cfg.appCheckDebugToken ? "debug token (local dev only)" : "not set — enable App Check in the Firebase console before submitting."), "ok");
    }
  })
  .catch((err) => setStatus(`Firebase failed to initialise: ${err.message}`, "warn"));
