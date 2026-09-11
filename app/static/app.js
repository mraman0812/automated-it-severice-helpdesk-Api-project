// Automated IT Helpdesk Dashboard Application - Vanilla JavaScript
const API_BASE = "/api/v1";

let currentToken = null;
let currentUser = null;
let currentTickets = [];
let activeTicket = null;
let currentFilter = "ALL";
let activeTab = "queue";

// Preset Passwords for Seeded Accounts
const USER_PASSWORDS = {
  "admin@example.com": "AdminPass123!",
  "manager@example.com": "ManagerPass123!",
  "network.agent@example.com": "AgentPass123!",
  "hardware.agent@example.com": "AgentPass123!",
  "rajan@example.com": "UserPass123!",
};

// Initial Startup
document.addEventListener("DOMContentLoaded", async () => {
  const switcher = document.getElementById("user-switcher");
  if (switcher) {
    await switchUser(switcher.value);
  }
});

// Toast System
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";

  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "❌";
  if (type === "warning") icon = "⚠️";

  toast.innerHTML = `
    <span style="font-size: 16px;">${icon}</span>
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// User Switching & JWT Authentication
async function switchUser(email) {
  const password = USER_PASSWORDS[email] || "UserPass123!";
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (res.ok) {
      currentToken = data.access_token;
      currentUser = data.user;

      // Update avatar letter
      const avatar = document.getElementById("current-user-avatar");
      if (avatar && currentUser) {
        avatar.innerText = (currentUser.name || currentUser.email)[0].toUpperCase();
      }

      showToast(`Signed in as ${currentUser.name} (${currentUser.role})`, "success");
      await refreshAll();
    } else {
      showToast(`Login failed for ${email}: ${data.detail || data.message || "Invalid credentials"}`, "error");
    }
  } catch (err) {
    console.error("Authentication error:", err);
    showToast(`Authentication error: ${err.message}`, "error");
  }
}

// Auth Fetch Wrapper
async function authFetch(url, options = {}) {
  const headers = options.headers || {};
  if (currentToken) {
    headers["Authorization"] = `Bearer ${currentToken}`;
  }
  return fetch(url, { ...options, headers });
}

// Refresh Entire Dashboard
async function refreshAll() {
  await Promise.all([
    loadStats(),
    loadTickets(),
    loadAnalytics(),
    loadModels(),
  ]);
}

// Tab Switching
function switchTab(tab) {
  activeTab = tab;
  const tabs = ["queue", "create", "analytics", "models"];

  tabs.forEach(t => {
    const navItem = document.getElementById(`nav-${t}`);
    const viewSection = document.getElementById(`view-${t}`);

    if (t === tab) {
      if (navItem) navItem.classList.add("active");
      if (viewSection) {
        if (t === "create") {
          viewSection.style.display = "grid";
        } else if (t === "analytics" || t === "models") {
          viewSection.style.display = "flex";
        } else {
          viewSection.style.display = "block";
        }
      }
    } else {
      if (navItem) navItem.classList.remove("active");
      if (viewSection) viewSection.style.display = "none";
    }
  });

  // Handle Human Review navigation highlight
  const navReview = document.getElementById("nav-review");
  if (navReview) {
    if (tab === "queue" && currentFilter === "REVIEW") {
      navReview.classList.add("active");
    } else {
      navReview.classList.remove("active");
    }
  }

  if (tab === "analytics") loadAnalytics();
  if (tab === "models") loadModels();
  if (tab === "queue") loadTickets();
}

// Load KPI Metrics
async function loadStats() {
  try {
    const [resStats, resSla] = await Promise.all([
      authFetch(`${API_BASE}/analytics/tickets`),
      authFetch(`${API_BASE}/analytics/sla`),
    ]);

    if (resStats.ok) {
      const stats = await resStats.json();
      const total = stats.total || 0;
      const active = (stats.open || 0) + (stats.assigned || 0) + (stats.in_progress || 0);
      const resolved = (stats.resolved || 0) + (stats.closed || 0);
      const review = stats.needs_review || 0;

      const elTotal = document.getElementById("stat-total");
      const elActive = document.getElementById("stat-active");
      const elResolved = document.getElementById("stat-resolved");
      const elReview = document.getElementById("stat-review");

      if (elTotal) elTotal.innerText = total;
      if (elActive) elActive.innerText = active;
      if (elResolved) elResolved.innerText = resolved;
      if (elReview) elReview.innerText = review;

      // Update sidebar badge
      const badgeTotal = document.getElementById("badge-total-tickets");
      const badgeReview = document.getElementById("badge-review-tickets");
      if (badgeTotal) badgeTotal.innerText = total;
      if (badgeReview) badgeReview.innerText = review;
    }

    if (resSla.ok) {
      const sla = await resSla.json();
      const elSla = document.getElementById("stat-sla");
      if (elSla) {
        const comp = typeof sla.sla_compliance === "number" ? sla.sla_compliance.toFixed(0) : "100";
        elSla.innerText = `${comp}%`;
      }
    }
  } catch (err) {
    console.error("Error loading KPI statistics:", err);
  }
}

// Load Tickets Table
async function loadTickets() {
  const tbody = document.getElementById("tickets-table-body");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">Fetching tickets from server...</td></tr>`;

  try {
    let url = `${API_BASE}/tickets?page=1&page_size=50`;
    if (currentFilter === "ACTIVE") url += "&status=IN_PROGRESS";
    if (currentFilter === "REVIEW") url += "&needs_review=true";
    if (currentFilter === "CRITICAL") url += "&priority=CRITICAL";
    if (currentFilter === "RESOLVED") url += "&status=RESOLVED";

    const res = await authFetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    currentTickets = data.items || [];
    renderTicketsTable(currentTickets);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 30px; color: var(--critical-text);">Failed to load tickets: ${escapeHtml(err.message)}</td></tr>`;
  }
}

// Render Tickets Table Rows
function renderTicketsTable(tickets) {
  const tbody = document.getElementById("tickets-table-body");
  if (!tbody) return;

  if (!tickets || tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">No tickets matching filter "${currentFilter}".</td></tr>`;
    return;
  }

  tbody.innerHTML = tickets.map(t => {
    const prio = (t.priority || "MEDIUM").toUpperCase();
    const status = (t.status || "OPEN").toUpperCase();
    const prioBadgeClass = `badge-${prio.toLowerCase()}`;
    const statusBadgeClass = `badge-${status.toLowerCase()}`;

    const confPct = Math.round((t.confidence_score || 0) * 100);
    const confBadge = t.needs_review
      ? `<span class="badge badge-review">⚠️ ${confPct}% (Review)</span>`
      : `<span class="badge badge-resolved">✓ ${confPct}%</span>`;

    const assigneeName = t.assignee ? escapeHtml(t.assignee.name) : `<span style="color: var(--text-muted); font-style: italic;">Unassigned</span>`;
    const categoryDisplay = escapeHtml(t.category_name || (t.classification && t.classification.category) || "General");
    const deptDisplay = escapeHtml(t.department_name || "IT Helpdesk");

    return `
      <tr onclick="openTicketModal(${t.id})">
        <td class="ticket-number-cell">${escapeHtml(t.ticket_number)}</td>
        <td class="ticket-title-cell">
          <div>${escapeHtml(t.title)}</div>
          <div class="ticket-desc-snippet">${escapeHtml(t.description)}</div>
        </td>
        <td style="font-weight: 600; color: #cbd5e1;">${categoryDisplay}</td>
        <td><span class="badge ${prioBadgeClass}">${prio}</span></td>
        <td>${deptDisplay}</td>
        <td>${assigneeName}</td>
        <td><span class="badge ${statusBadgeClass}">${status}</span></td>
        <td>${confBadge}</td>
        <td style="text-align: right;">
          <button class="btn btn-secondary" style="padding: 5px 12px; font-size: 11px;" onclick="event.stopPropagation(); openTicketModal(${t.id})">Inspect</button>
        </td>
      </tr>
    `;
  }).join("");
}

// Filter Ticket Queue
function filterTickets(filter) {
  currentFilter = filter;
  const filters = ["ALL", "ACTIVE", "REVIEW", "CRITICAL", "RESOLVED"];

  filters.forEach(f => {
    const chip = document.getElementById(`filter-${f}`);
    if (chip) {
      if (f === filter) chip.classList.add("active");
      else chip.classList.remove("active");
    }
  });

  const navReview = document.getElementById("nav-review");
  if (navReview) {
    if (filter === "REVIEW") navReview.classList.add("active");
    else navReview.classList.remove("active");
  }

  loadTickets();
}

// Instant Live Search
let searchDebounceTimer;
function handleSearch(e) {
  clearTimeout(searchDebounceTimer);
  const q = e.target.value.trim();

  searchDebounceTimer = setTimeout(async () => {
    if (!q) {
      loadTickets();
      return;
    }

    try {
      const res = await authFetch(`${API_BASE}/tickets/search?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        renderTicketsTable(data.items || []);
      }
    } catch (err) {
      console.error("Search error:", err);
    }
  }, 250);
}

// Preset Test Scenarios
function fillSample(type) {
  const samples = {
    vpn: {
      title: "Cannot connect to corporate VPN from home",
      desc: "Working remotely and Cisco AnyConnect refuses to establish the tunnel. Authentication completes but connection drops immediately with error 412.",
    },
    hardware: {
      title: "Laptop battery swollen and pushing trackpad",
      desc: "Chassis on my ThinkPad is bulging noticeably and the trackpad cannot be clicked. Urgent safety hazard and overheating.",
    },
    password: {
      title: "Forgot my domain password after holidays",
      desc: "Returned to the office today and cannot login to Windows workstation. Self service password portal is not responding to reset SMS.",
    },
    outage: {
      title: "Core production PostgreSQL database down",
      desc: "Connection pool exhausted and all API microservices returning 502 Bad Gateway. Complete company-wide customer service interruption.",
    },
  };

  if (samples[type]) {
    document.getElementById("new-title").value = samples[type].title;
    document.getElementById("new-description").value = samples[type].desc;
    showToast(`Loaded "${samples[type].title}" template`, "info");
  }
}

// Test AI Prediction Sandbox Only
async function testPredictionOnly() {
  const title = document.getElementById("new-title").value.trim();
  const desc = document.getElementById("new-description").value.trim();

  if (!title || !desc) {
    showToast("Please provide both title and description to run inference.", "warning");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/classification/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description: desc }),
    });

    if (!res.ok) throw new Error("Inference failed");

    const data = await res.json();

    const placeholder = document.getElementById("ai-placeholder");
    const results = document.getElementById("ai-results");
    if (placeholder) placeholder.style.display = "none";
    if (results) results.style.display = "block";

    document.getElementById("ai-res-category").innerText = data.category || "Unknown";
    document.getElementById("ai-res-subcategory").innerText = `Subcategory: ${data.subcategory || "General"}`;
    document.getElementById("ai-res-dept").innerText = data.department || "IT Support";
    document.getElementById("ai-res-prio").innerText = data.priority || "MEDIUM";

    const confPct = Math.round((data.confidence || 0) * 100);
    document.getElementById("ai-res-conf").innerText = `${confPct}%`;
    const confBar = document.getElementById("ai-res-conf-bar");
    if (confBar) confBar.style.width = `${confPct}%`;

    const flagEl = document.getElementById("ai-res-flag");
    if (data.needs_review) {
      flagEl.innerHTML = `<span style="color: #c084fc; font-weight: 600;">⚠️ Needs Human Review: Confidence below threshold (&lt;80%)</span>`;
      if (confBar) confBar.style.background = "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)";
    } else {
      flagEl.innerHTML = `<span style="color: #34d399; font-weight: 600;">✓ High Confidence: Direct routing to ${escapeHtml(data.department)}</span>`;
      if (confBar) confBar.style.background = "var(--accent-gradient-blue)";
    }

    showToast(`AI classified as ${data.category} / ${data.priority} (${confPct}%)`, "success");
  } catch (err) {
    showToast(`Prediction failed: ${err.message}`, "error");
  }
}

// Submit New Ticket
async function submitNewTicket() {
  const title = document.getElementById("new-title").value.trim();
  const desc = document.getElementById("new-description").value.trim();

  if (!title || !desc) {
    showToast("Please provide both title and description.", "warning");
    return;
  }

  try {
    const res = await authFetch(`${API_BASE}/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description: desc }),
    });

    const data = await res.json();
    if (res.ok) {
      showToast(`Ticket ${data.ticket_number} created and classified!`, "success");
      document.getElementById("new-title").value = "";
      document.getElementById("new-description").value = "";

      switchTab("queue");
      await refreshAll();
      openTicketModal(data.id);
    } else {
      showToast(`Ticket creation failed: ${data.detail || data.message || "Error"}`, "error");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

// Open Ticket Detail Modal
async function openTicketModal(ticketId) {
  try {
    const res = await authFetch(`${API_BASE}/tickets/${ticketId}`);
    if (!res.ok) throw new Error("Could not load ticket details");
    activeTicket = await res.json();

    document.getElementById("modal-ticket-id").innerText = activeTicket.ticket_number;

    const modalStatus = document.getElementById("modal-status-badge");
    modalStatus.className = `badge badge-${(activeTicket.status || 'open').toLowerCase()}`;
    modalStatus.innerText = activeTicket.status;

    const modalPrio = document.getElementById("modal-priority-badge");
    modalPrio.className = `badge badge-${(activeTicket.priority || 'medium').toLowerCase()}`;
    modalPrio.innerText = activeTicket.priority;

    document.getElementById("modal-title").innerText = activeTicket.title;
    document.getElementById("modal-desc").innerText = activeTicket.description;

    document.getElementById("modal-category").innerText = activeTicket.category_name || (activeTicket.classification && activeTicket.classification.category) || "-";
    document.getElementById("modal-department").innerText = activeTicket.department_name || "-";
    document.getElementById("modal-agent").innerText = activeTicket.assignee ? activeTicket.assignee.name : "Unassigned";

    const confPct = Math.round((activeTicket.confidence_score || 0) * 100);
    document.getElementById("modal-confidence").innerText = `${confPct}%`;

    // Pre-select category and priority in correction dropdowns
    const corrCat = document.getElementById("corr-cat");
    const corrPrio = document.getElementById("corr-prio");
    if (corrCat && activeTicket.category_name) corrCat.value = activeTicket.category_name;
    if (corrPrio && activeTicket.priority) corrPrio.value = activeTicket.priority;

    // Render Lifecycle Action Buttons
    renderActionButtons();

    // Load Comments Thread
    loadComments(activeTicket.id);

    // Open Modal Overlay
    const modal = document.getElementById("ticket-modal");
    if (modal) modal.classList.add("active");
  } catch (err) {
    showToast(`Failed to open ticket: ${err.message}`, "error");
  }
}

// Close Modal
function closeModal() {
  const modal = document.getElementById("ticket-modal");
  if (modal) modal.classList.remove("active");
  activeTicket = null;
}

// Render Lifecycle Action Buttons
function renderActionButtons() {
  const container = document.getElementById("modal-actions-container");
  if (!container || !activeTicket) return;

  const buttons = [];
  const status = activeTicket.status;

  if (status !== "RESOLVED" && status !== "CLOSED") {
    buttons.push(`
      <button onclick="resolveTicketAction()" class="btn btn-success" style="padding: 7px 14px; font-size: 12px;">
        ✓ Resolve Ticket
      </button>
    `);
  }

  if (status === "RESOLVED") {
    buttons.push(`
      <button onclick="closeTicketAction()" class="btn btn-secondary" style="padding: 7px 14px; font-size: 12px;">
        🔒 Close Ticket
      </button>
    `);
  }

  if (status === "RESOLVED" || status === "CLOSED") {
    buttons.push(`
      <button onclick="reopenTicketAction()" class="btn btn-secondary" style="padding: 7px 14px; font-size: 12px; color: #f472b6;">
        🔄 Reopen Ticket
      </button>
    `);
  }

  container.innerHTML = buttons.length ? buttons.join("") : `<span style="font-size: 12px; color: var(--text-muted);">No lifecycle actions available in current state.</span>`;
}

// Resolve Ticket
async function resolveTicketAction() {
  const resolution = prompt("Enter resolution notes:", "Investigated and problem has been verified as fixed.");
  if (!resolution) return;

  try {
    const res = await authFetch(`${API_BASE}/tickets/${activeTicket.id}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolution }),
    });

    if (res.ok) {
      showToast("Ticket marked as RESOLVED", "success");
      await openTicketModal(activeTicket.id);
      await refreshAll();
    } else {
      const err = await res.json();
      showToast(err.detail || "Failed to resolve ticket", "error");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Close Ticket
async function closeTicketAction() {
  try {
    const res = await authFetch(`${API_BASE}/tickets/${activeTicket.id}/close`, { method: "POST" });
    if (res.ok) {
      showToast("Ticket CLOSED permanently", "info");
      await openTicketModal(activeTicket.id);
      await refreshAll();
    } else {
      const err = await res.json();
      showToast(err.detail || "Failed to close ticket", "error");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Reopen Ticket
async function reopenTicketAction() {
  try {
    const res = await authFetch(`${API_BASE}/tickets/${activeTicket.id}/reopen`, { method: "POST" });
    if (res.ok) {
      showToast("Ticket REOPENED", "warning");
      await openTicketModal(activeTicket.id);
      await refreshAll();
    } else {
      const err = await res.json();
      showToast(err.detail || "Failed to reopen ticket", "error");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Human-In-The-Loop Feedback Correction
async function submitHumanCorrection() {
  if (!activeTicket) return;

  const correct_category = document.getElementById("corr-cat").value;
  const correct_priority = document.getElementById("corr-prio").value;

  try {
    const res = await authFetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticket_id: activeTicket.id,
        correct_category,
        correct_priority,
        comments: "Manual human override via dashboard UI",
      }),
    });

    if (res.ok) {
      showToast(`Correction submitted: ${correct_category} / ${correct_priority}`, "success");
      await openTicketModal(activeTicket.id);
      await refreshAll();
    } else {
      const err = await res.json();
      showToast(err.detail || "Failed to submit correction", "error");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Comments Thread
async function loadComments(ticketId) {
  const container = document.getElementById("modal-comments");
  if (!container) return;

  try {
    const res = await authFetch(`${API_BASE}/tickets/${ticketId}/comments`);
    if (!res.ok) return;

    const comments = await res.json();
    if (!comments || comments.length === 0) {
      container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); padding: 8px 0;">No comments logged yet.</div>`;
      return;
    }

    container.innerHTML = comments.map(c => `
      <div style="background: rgba(0, 0, 0, 0.35); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 10px 12px;">
        <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
          <span style="font-weight: 700; color: #a5b4fc;">${escapeHtml(c.user ? c.user.name : "System")}</span>
          <span style="color: var(--text-muted); font-family: 'JetBrains Mono'; font-size: 10px;">${new Date(c.created_at).toLocaleString()}</span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); white-space: pre-wrap;">${escapeHtml(c.comment)}</div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading comments:", err);
  }
}

async function postComment() {
  const input = document.getElementById("comment-input");
  if (!input || !activeTicket) return;

  const comment = input.value.trim();
  if (!comment) return;

  try {
    const res = await authFetch(`${API_BASE}/tickets/${activeTicket.id}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment, is_internal: false }),
    });

    if (res.ok) {
      input.value = "";
      showToast("Comment logged", "info");
      loadComments(activeTicket.id);
    } else {
      const err = await res.json();
      showToast(err.detail || "Failed to post comment", "error");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Analytics Visualizations
async function loadAnalytics() {
  try {
    const [resCats, resPrios, resWorkloads] = await Promise.all([
      authFetch(`${API_BASE}/analytics/categories`),
      authFetch(`${API_BASE}/analytics/priorities`),
      authFetch(`${API_BASE}/analytics/agents`),
    ]);

    if (resCats.ok) {
      const data = await resCats.json();
      renderBarChart("category-bars", data.distribution || {});
    }

    if (resPrios.ok) {
      const data = await resPrios.json();
      renderBarChart("priority-bars", data.distribution || {});
    }

    if (resWorkloads.ok) {
      const workloads = await resWorkloads.json();
      renderWorkloadTable(workloads || []);
    }
  } catch (err) {
    console.error("Error loading analytics:", err);
  }
}

function renderBarChart(containerId, dataMap) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const entries = Object.entries(dataMap);
  if (entries.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 20px;">No distribution data recorded.</div>`;
    return;
  }

  const maxVal = Math.max(1, ...entries.map(([_, v]) => v));

  container.innerHTML = entries.map(([label, val]) => {
    const pct = Math.round((val / maxVal) * 100);
    return `
      <div class="bar-row">
        <div class="bar-row-header">
          <span style="color: var(--text-secondary);">${escapeHtml(label)}</span>
          <span style="font-family: 'JetBrains Mono'; color: #a5b4fc;">${val}</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%;"></div>
        </div>
      </div>
    `;
  }).join("");
}

function renderWorkloadTable(workloads) {
  const tbody = document.getElementById("workload-tbody");
  if (!tbody) return;

  if (workloads.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No technicians registered.</td></tr>`;
    return;
  }

  tbody.innerHTML = workloads.map(w => {
    const isHeavy = w.active_tickets >= 3;
    const statusTag = isHeavy
      ? `<span class="badge badge-high">Heavy Queue</span>`
      : `<span class="badge badge-resolved">Available</span>`;

    return `
      <tr>
        <td style="font-weight: 700; color: white;">${escapeHtml(w.agent_name)}</td>
        <td>${escapeHtml(w.department_name || "Support")}</td>
        <td style="font-family: 'JetBrains Mono'; font-weight: 700; color: #818cf8;">${w.active_tickets}</td>
        <td style="font-family: 'JetBrains Mono'; font-weight: 700; color: #34d399;">${w.resolved_tickets}</td>
        <td>${statusTag}</td>
      </tr>
    `;
  }).join("");
}

// ML Model Management & Retraining
async function loadModels() {
  try {
    const [resModels, resRuns] = await Promise.all([
      authFetch(`${API_BASE}/models`),
      authFetch(`${API_BASE}/models/training-runs/history`),
    ]);

    if (resModels.ok) {
      const models = await resModels.json();
      const active = models.find(m => m.status === "ACTIVE") || models[0];
      if (active) {
        const acc = document.getElementById("ml-stat-acc");
        const f1 = document.getElementById("ml-stat-f1");
        if (acc) acc.innerText = `${Math.round((active.accuracy || 0.985) * 1000) / 10}%`;
        if (f1) f1.innerText = `${Math.round((active.f1_score || 0.981) * 1000) / 10}%`;
      }
    }

    if (resRuns.ok) {
      const runs = await resRuns.json();
      const tbody = document.getElementById("runs-tbody");
      if (tbody) {
        if (!runs || runs.length === 0) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--text-muted);">No training runs recorded yet.</td></tr>`;
        } else {
          tbody.innerHTML = runs.map(r => `
            <tr>
              <td class="ticket-number-cell">#RUN-${r.id}</td>
              <td style="font-weight: 600; color: #c084fc;">${escapeHtml(r.dataset_version)}</td>
              <td style="font-family: 'JetBrains Mono';">${r.training_samples} / ${r.test_samples}</td>
              <td style="font-family: 'JetBrains Mono'; font-weight: 700; color: #34d399;">${Math.round((r.accuracy || 0) * 1000) / 10}%</td>
              <td style="font-family: 'JetBrains Mono'; color: var(--text-muted);">${r.training_duration_seconds ? r.training_duration_seconds + 's' : '-'}</td>
              <td><span class="badge badge-resolved">${escapeHtml(r.status)}</span></td>
            </tr>
          `).join("");
        }
      }
    }
  } catch (err) {
    console.error("Error loading model stats:", err);
  }
}

// Trigger Retraining
async function triggerRetraining() {
  const algoEl = document.getElementById("train-algorithm");
  const feedbackEl = document.getElementById("train-feedback");
  const btn = document.getElementById("btn-retrain");

  const algorithm = algoEl ? algoEl.value : "LogisticRegression";

  btn.disabled = true;
  feedbackEl.innerText = "⏳ Retraining models with augmented feedback dataset...";
  feedbackEl.style.color = "#a5b4fc";

  try {
    const res = await authFetch(`${API_BASE}/models/train`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ algorithm }),
    });

    const data = await res.json();
    if (res.ok) {
      feedbackEl.innerText = `✓ Retrained successfully! New Version: ${data.version}, Accuracy: ${(data.accuracy * 100).toFixed(1)}%`;
      feedbackEl.style.color = "#34d399";
      showToast(`Model retrained successfully (${data.version})`, "success");
      await loadModels();
    } else {
      feedbackEl.innerText = `Error: ${data.detail || data.message || "Failed"}`;
      feedbackEl.style.color = "#fda4af";
      showToast("Training failed", "error");
    }
  } catch (err) {
    feedbackEl.innerText = `Error: ${err.message}`;
    feedbackEl.style.color = "#fda4af";
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
}

// Escape HTML utility
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
