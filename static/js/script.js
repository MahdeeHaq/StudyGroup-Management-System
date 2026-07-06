// ============================================================
// Study Group Management System — frontend logic
// Talks to the Flask API defined in app.py
// ============================================================

const state = { subjects: [], members: [], groups: [] };

// ---------------- Tabs ----------------
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`panel-${tab.dataset.tab}`).classList.add("active");
  });
});

// ---------------- Toast ----------------
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2600);
}

// ---------------- Fetch helper ----------------
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

// ---------------- Modal ----------------
const backdrop = document.getElementById("modal-backdrop");
const modalTitle = document.getElementById("modal-title");
const modalBody = document.getElementById("modal-body");

function openModal(title, bodyHtml) {
  modalTitle.textContent = title;
  modalBody.innerHTML = bodyHtml;
  backdrop.classList.add("active");
}
function closeModal() { backdrop.classList.remove("active"); }
document.getElementById("modal-close").addEventListener("click", closeModal);
backdrop.addEventListener("click", e => { if (e.target === backdrop) closeModal(); });

// ============================================================
// SUBJECTS
// ============================================================
async function loadSubjects() {
  state.subjects = await api("/api/subjects");
  renderSubjectsTable();
  renderSubjectOptions();
}

function renderSubjectsTable() {
  const tbody = document.querySelector("#subjects-table tbody");
  if (state.subjects.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="empty-state">No subjects yet. Add one to get started.</td></tr>`;
    return;
  }
  tbody.innerHTML = state.subjects.map(s => `
    <tr>
      <td>${s.subject_code}</td>
      <td>${s.subject_name}</td>
      <td class="row-actions">
        <button onclick="editSubject(${s.subject_id})">Edit</button>
        <button class="danger" onclick="deleteSubject(${s.subject_id})">Delete</button>
      </td>
    </tr>
  `).join("");
}

function renderSubjectOptions() {
  const filter = document.getElementById("subject-filter");
  filter.innerHTML = `<option value="">All subjects</option>` +
    state.subjects.map(s => `<option value="${s.subject_id}">${s.subject_name}</option>`).join("");
}

function subjectFormHtml(subject = {}) {
  return `
    <div class="field"><label>Subject code</label>
      <input id="f-subject-code" value="${subject.subject_code || ""}" placeholder="e.g. CSE-224"></div>
    <div class="field"><label>Subject name</label>
      <input id="f-subject-name" value="${subject.subject_name || ""}" placeholder="e.g. Database Management System"></div>
    <div class="modal-footer">
      <button class="btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn-primary" id="btn-save-subject">Save</button>
    </div>`;
}

document.getElementById("btn-new-subject").addEventListener("click", () => {
  openModal("New subject", subjectFormHtml());
  document.getElementById("btn-save-subject").addEventListener("click", () => saveSubject(null));
});

window.editSubject = (id) => {
  const subject = state.subjects.find(s => s.subject_id === id);
  openModal("Edit subject", subjectFormHtml(subject));
  document.getElementById("btn-save-subject").addEventListener("click", () => saveSubject(id));
};

async function saveSubject(id) {
  const payload = {
    subject_code: document.getElementById("f-subject-code").value.trim(),
    subject_name: document.getElementById("f-subject-name").value.trim(),
  };
  try {
    if (id) await api(`/api/subjects/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/api/subjects", { method: "POST", body: JSON.stringify(payload) });
    closeModal();
    showToast(id ? "Subject updated" : "Subject added");
    await loadSubjects();
    await loadGroups();
  } catch (e) { showToast(e.message, true); }
}

window.deleteSubject = async (id) => {
  if (!confirm("Delete this subject?")) return;
  try {
    await api(`/api/subjects/${id}`, { method: "DELETE" });
    showToast("Subject deleted");
    await loadSubjects();
  } catch (e) { showToast(e.message, true); }
};

// ============================================================
// MEMBERS
// ============================================================
async function loadMembers() {
  state.members = await api("/api/members");
  renderMembersTable();
}

function renderMembersTable() {
  const tbody = document.querySelector("#members-table tbody");
  if (state.members.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No members yet. Add one to get started.</td></tr>`;
    return;
  }
  tbody.innerHTML = state.members.map(m => `
    <tr>
      <td>${m.full_name}</td>
      <td>${m.email}</td>
      <td>${m.phone || "—"}</td>
      <td class="row-actions">
        <button onclick="editMember(${m.member_id})">Edit</button>
        <button class="danger" onclick="deleteMember(${m.member_id})">Delete</button>
      </td>
    </tr>
  `).join("");
}

function memberFormHtml(member = {}) {
  return `
    <div class="field"><label>Full name</label>
      <input id="f-member-name" value="${member.full_name || ""}" placeholder="e.g. Mahdee Haque"></div>
    <div class="field"><label>Email</label>
      <input id="f-member-email" value="${member.email || ""}" placeholder="name@example.com"></div>
    <div class="field"><label>Phone</label>
      <input id="f-member-phone" value="${member.phone || ""}" placeholder="Optional"></div>
    <div class="modal-footer">
      <button class="btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn-primary" id="btn-save-member">Save</button>
    </div>`;
}

document.getElementById("btn-new-member").addEventListener("click", () => {
  openModal("New member", memberFormHtml());
  document.getElementById("btn-save-member").addEventListener("click", () => saveMember(null));
});

window.editMember = (id) => {
  const member = state.members.find(m => m.member_id === id);
  openModal("Edit member", memberFormHtml(member));
  document.getElementById("btn-save-member").addEventListener("click", () => saveMember(id));
};

async function saveMember(id) {
  const payload = {
    full_name: document.getElementById("f-member-name").value.trim(),
    email: document.getElementById("f-member-email").value.trim(),
    phone: document.getElementById("f-member-phone").value.trim(),
  };
  try {
    if (id) await api(`/api/members/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/api/members", { method: "POST", body: JSON.stringify(payload) });
    closeModal();
    showToast(id ? "Member updated" : "Member added");
    await loadMembers();
    await loadGroups();
  } catch (e) { showToast(e.message, true); }
}

window.deleteMember = async (id) => {
  if (!confirm("Delete this member?")) return;
  try {
    await api(`/api/members/${id}`, { method: "DELETE" });
    showToast("Member deleted");
    await loadMembers();
    await loadGroups();
  } catch (e) { showToast(e.message, true); }
};

// ============================================================
// STUDY GROUPS
// ============================================================
async function loadGroups() {
  const filterVal = document.getElementById("subject-filter").value;
  const query = filterVal ? `?subject_id=${filterVal}` : "";
  state.groups = await api(`/api/groups${query}`);
  renderGroups();
}

document.getElementById("subject-filter").addEventListener("change", loadGroups);

function fmtDateTime(dt) {
  const d = new Date(dt.replace(" ", "T"));
  if (isNaN(d)) return dt;
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function renderGroups() {
  const list = document.getElementById("groups-list");
  if (state.groups.length === 0) {
    list.innerHTML = `<div class="empty-state">No study groups yet. Create one to get started.</div>`;
    return;
  }
  list.innerHTML = state.groups.map(g => `
    <div class="group-card">
      <div class="card-top">
        <div>
          <h3>${g.group_name}</h3>
          <div class="subject-code">${g.subject_code} · ${g.subject_name}</div>
        </div>
        <span class="status-badge status-${g.status}">${g.status}</span>
      </div>
      <div class="meta">
        <div>📅 ${fmtDateTime(g.meeting_time)}</div>
        <div>📍 ${g.location}</div>
        <div>🧑‍🏫 Organizer: ${g.organizer_name}</div>
      </div>
      ${g.description ? `<div class="desc">${g.description}</div>` : ""}
      <div class="members">
        ${g.members.map(m => `
          <span class="member-chip">${m.full_name}
            <button onclick="removeMemberFromGroup(${g.group_id}, ${m.member_id})" title="Remove">✕</button>
          </span>`).join("") || `<span class="member-chip" style="opacity:.5">No members joined</span>`}
        <span class="member-chip" style="cursor:pointer" onclick="openAddMember(${g.group_id})">+ Add member</span>
      </div>
      <div class="card-actions">
        <button class="btn-secondary" onclick="editGroup(${g.group_id})">Edit</button>
        <button class="btn-danger" onclick="deleteGroup(${g.group_id})">Delete</button>
      </div>
    </div>
  `).join("");
}

function groupFormHtml(group = {}) {
  const subjectOpts = state.subjects.map(s =>
    `<option value="${s.subject_id}" ${group.subject_id === s.subject_id ? "selected" : ""}>${s.subject_name}</option>`
  ).join("");
  const memberOpts = state.members.map(m =>
    `<option value="${m.member_id}" ${group.organizer_id === m.member_id ? "selected" : ""}>${m.full_name}</option>`
  ).join("");
  const dt = group.meeting_time ? group.meeting_time.replace(" ", "T").slice(0, 16) : "";

  return `
    <div class="field"><label>Group name</label>
      <input id="f-group-name" value="${group.group_name || ""}" placeholder="e.g. DBMS Lab Revision"></div>
    <div class="field"><label>Subject</label>
      <select id="f-group-subject">${subjectOpts || "<option value=''>Add a subject first</option>"}</select></div>
    <div class="field"><label>Organizer</label>
      <select id="f-group-organizer">${memberOpts || "<option value=''>Add a member first</option>"}</select></div>
    <div class="field"><label>Meeting time</label>
      <input type="datetime-local" id="f-group-time" value="${dt}"></div>
    <div class="field"><label>Location</label>
      <input id="f-group-location" value="${group.location || ""}" placeholder="e.g. Library Room 3"></div>
    <div class="field"><label>Description</label>
      <textarea id="f-group-desc" rows="2" placeholder="Optional notes">${group.description || ""}</textarea></div>
    <div class="field"><label>Status</label>
      <select id="f-group-status">
        ${["Scheduled", "Ongoing", "Completed", "Cancelled"].map(s =>
          `<option value="${s}" ${group.status === s ? "selected" : ""}>${s}</option>`).join("")}
      </select></div>
    <div class="modal-footer">
      <button class="btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn-primary" id="btn-save-group">Save</button>
    </div>`;
}

document.getElementById("btn-new-group").addEventListener("click", () => {
  if (state.subjects.length === 0 || state.members.length === 0) {
    showToast("Add at least one subject and one member first", true);
    return;
  }
  openModal("New study group", groupFormHtml());
  document.getElementById("btn-save-group").addEventListener("click", () => saveGroup(null));
});

window.editGroup = (id) => {
  const group = state.groups.find(g => g.group_id === id);
  openModal("Edit study group", groupFormHtml(group));
  document.getElementById("btn-save-group").addEventListener("click", () => saveGroup(id));
};

async function saveGroup(id) {
  const payload = {
    group_name: document.getElementById("f-group-name").value.trim(),
    subject_id: document.getElementById("f-group-subject").value,
    organizer_id: document.getElementById("f-group-organizer").value,
    meeting_time: document.getElementById("f-group-time").value.replace("T", " ") + ":00",
    location: document.getElementById("f-group-location").value.trim(),
    description: document.getElementById("f-group-desc").value.trim(),
    status: document.getElementById("f-group-status").value,
  };
  try {
    if (id) await api(`/api/groups/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/api/groups", { method: "POST", body: JSON.stringify(payload) });
    closeModal();
    showToast(id ? "Study group updated" : "Study group created");
    await loadGroups();
  } catch (e) { showToast(e.message, true); }
}

window.deleteGroup = async (id) => {
  if (!confirm("Delete this study group?")) return;
  try {
    await api(`/api/groups/${id}`, { method: "DELETE" });
    showToast("Study group deleted");
    await loadGroups();
  } catch (e) { showToast(e.message, true); }
};

// ---- membership ----
window.openAddMember = (groupId) => {
  const group = state.groups.find(g => g.group_id === groupId);
  const joinedIds = new Set(group.members.map(m => m.member_id));
  const options = state.members.filter(m => !joinedIds.has(m.member_id));

  if (options.length === 0) {
    showToast("All members are already in this group", true);
    return;
  }

  openModal("Add member to group", `
    <div class="field"><label>Member</label>
      <select id="f-add-member">
        ${options.map(m => `<option value="${m.member_id}">${m.full_name}</option>`).join("")}
      </select>
    </div>
    <div class="modal-footer">
      <button class="btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn-primary" id="btn-confirm-add-member">Add</button>
    </div>
  `);
  document.getElementById("btn-confirm-add-member").addEventListener("click", async () => {
    const memberId = document.getElementById("f-add-member").value;
    try {
      await api(`/api/groups/${groupId}/members`, { method: "POST", body: JSON.stringify({ member_id: memberId }) });
      closeModal();
      showToast("Member added");
      await loadGroups();
    } catch (e) { showToast(e.message, true); }
  });
};

window.removeMemberFromGroup = async (groupId, memberId) => {
  try {
    await api(`/api/groups/${groupId}/members/${memberId}`, { method: "DELETE" });
    showToast("Member removed");
    await loadGroups();
  } catch (e) { showToast(e.message, true); }
};

// ---------------- Init ----------------
(async function init() {
  try {
    await loadSubjects();
    await loadMembers();
    await loadGroups();
  } catch (e) {
    showToast("Could not connect to the server. Is Flask running?", true);
  }
})();
