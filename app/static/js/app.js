const state = {
  token: localStorage.getItem("edu_token") || null,
  user: JSON.parse(localStorage.getItem("edu_user") || "null"),
  role: localStorage.getItem("edu_role") || null,
  universities: [],
};

const authPanel = document.getElementById("authPanel");
const dashboardPanel = document.getElementById("dashboardPanel");
const dashboardTitle = document.getElementById("dashboardTitle");
const actionsEl = document.getElementById("actions");
const contentGrid = document.getElementById("contentGrid");
const sessionArea = document.getElementById("sessionArea");
const loadingOverlay = document.getElementById("loadingOverlay");
const toast = document.getElementById("toast");

function setLoading(isLoading) {
  loadingOverlay.classList.toggle("hidden", !isLoading);
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  toast.classList.toggle("error", isError);
  setTimeout(() => toast.classList.add("hidden"), 2600);
}

async function api(path, options = {}) {
  setLoading(true);
  try {
    const headers = { ...(options.headers || {}) };
    if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const response = await fetch(path, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || data.error || "Request failed");
    return data;
  } finally {
    setLoading(false);
  }
}

async function downloadFile(path, filenameFallback) {
  setLoading(true);
  try {
    const headers = {};
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const response = await fetch(path, { headers });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.message || "Download failed");
    }
    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const parsed = disposition.match(/filename=([^;]+)/i);
    const filename = parsed ? parsed[1].replace(/"/g, "") : filenameFallback;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } finally {
    setLoading(false);
  }
}

function makeCard(title, subtitle = "") {
  const node = document.createElement("article");
  node.className = "card";
  node.innerHTML = `<h3>${title}</h3>${subtitle ? `<p>${subtitle}</p>` : ""}`;
  return node;
}

function metricGrid(items) {
  const wrap = document.createElement("div");
  wrap.className = "metrics";
  items.forEach((i) => {
    const el = document.createElement("div");
    el.className = "metric";
    el.innerHTML = `<small>${i.label}</small><strong>${i.value}</strong>`;
    wrap.appendChild(el);
  });
  return wrap;
}

function table(columns, rows) {
  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  const t = document.createElement("table");
  t.className = "data-table";
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  columns.forEach((c) => {
    const th = document.createElement("th");
    th.textContent = c.label;
    trh.appendChild(th);
  });
  thead.appendChild(trh);
  t.appendChild(thead);
  const tbody = document.createElement("tbody");
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    columns.forEach((c) => {
      const td = document.createElement("td");
      td.textContent = r[c.key] ?? "-";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  t.appendChild(tbody);
  wrap.appendChild(t);
  return wrap;
}

function list(items = []) {
  const ul = document.createElement("ul");
  ul.className = "plain-list";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });
  return ul;
}

function statusPill(value) {
  const span = document.createElement("span");
  span.className = "chip";
  span.textContent = value;
  return span;
}

function clearContent() {
  contentGrid.innerHTML = "";
}

function setSessionArea() {
  if (!state.user) {
    sessionArea.innerHTML = "";
    return;
  }
  const uniChip = state.user.university_name ? `<span class="chip">${state.user.university_name}</span>` : "";
  sessionArea.innerHTML = `${state.user.name} <span class="chip">${state.role}</span>${uniChip}`;
}

function persistSession() {
  if (state.token) localStorage.setItem("edu_token", state.token);
  if (state.user) localStorage.setItem("edu_user", JSON.stringify(state.user));
  if (state.role) localStorage.setItem("edu_role", state.role);
}

function clearSession() {
  state.token = null;
  state.user = null;
  state.role = null;
  localStorage.removeItem("edu_token");
  localStorage.removeItem("edu_user");
  localStorage.removeItem("edu_role");
}

async function login(identifier, password, universityId) {
  const res = await api("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password, university_id: Number(universityId) }),
  });
  state.token = res.data.access_token;
  state.user = res.data.user;
  state.role = res.data.user.role;
  persistSession();
  renderApp();
  showToast("Login successful");
}

function renderApp() {
  setSessionArea();
  const authenticated = Boolean(state.token && state.user);
  authPanel.classList.toggle("hidden", authenticated);
  dashboardPanel.classList.toggle("hidden", !authenticated);
  if (!authenticated) return;
  dashboardTitle.textContent = `${state.role} Dashboard`;
  renderActionsByRole();
}

function setActionButtons(actions) {
  actionsEl.innerHTML = "";
  actions.forEach((item, idx) => {
    const btn = document.createElement("button");
    btn.className = `action-btn ${idx === 0 ? "active" : ""}`;
    btn.textContent = item.label;
    btn.onclick = async () => {
      [...actionsEl.children].forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      try {
        await item.run();
      } catch (err) {
        showToast(err.message, true);
      }
    };
    actionsEl.appendChild(btn);
  });
  if (actions[0]) actions[0].run();
}

async function loadUniversityOptions() {
  const select = document.getElementById("universityId");
  select.innerHTML = `<option value="">Select university</option>`;
  try {
    const res = await api("/api/auth/universities");
    state.universities = res.data || [];
    state.universities.forEach((u) => {
      const option = document.createElement("option");
      option.value = String(u.university_id);
      option.textContent = `${u.name} (${u.location})`;
      select.appendChild(option);
    });
    if (state.universities.length === 1) {
      select.value = String(state.universities[0].university_id);
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

async function renderAdminOverview() {
  clearContent();
  const [statsRes, refRes] = await Promise.all([api("/api/admin/system-stats"), api("/api/admin/reference-data")]);
  const stats = statsRes.data;
  const hierarchy = refRes.data || [];

  const top = makeCard("Institution Summary");
  top.appendChild(
    metricGrid([
      { label: "Students", value: stats.students },
      { label: "Faculties", value: stats.faculties },
      { label: "Departments", value: stats.departments },
      { label: "Courses", value: stats.courses },
    ])
  );
  contentGrid.appendChild(top);

  const trend = makeCard("Performance Trend");
  trend.appendChild(
    table(
      [
        { key: "session", label: "Session" },
        { key: "average_score", label: "Average Score" },
      ],
      stats.institution_trend || []
    )
  );
  contentGrid.appendChild(trend);

  const hierarchyCard = makeCard("Institution Structure");
  const rows = [];
  hierarchy.forEach((u) => {
    (u.faculties || []).forEach((f) => {
      (f.departments || []).forEach((d) => {
        rows.push({
          university: u.name,
          faculty: f.name,
          department: d.name,
          department_id: d.department_id,
        });
      });
    });
  });
  hierarchyCard.appendChild(
    table(
      [
        { key: "university", label: "University" },
        { key: "faculty", label: "Faculty" },
        { key: "department", label: "Department" },
        { key: "department_id", label: "Dept ID" },
      ],
      rows
    )
  );
  contentGrid.appendChild(hierarchyCard);
}

function promptJSON(fields) {
  const data = {};
  for (const f of fields) {
    const input = prompt(`${f.label}${f.required ? "" : " (optional)"}`);
    if (f.required && (input === null || input.trim() === "")) return null;
    if (input !== null && input.trim() !== "") data[f.key] = f.type === "number" ? Number(input) : input.trim();
  }
  return data;
}

async function renderAdminActions() {
  setActionButtons([
    { label: "Overview", run: renderAdminOverview },
    {
      label: "Auto Setup",
      run: async () => {
        const payload = promptJSON([
          { key: "university_name", label: "University name", required: false },
          { key: "location", label: "Location", required: false },
          { key: "established_year", label: "Established year", required: false, type: "number" },
          { key: "faculty_name", label: "Faculty name", required: false },
          { key: "department_name", label: "Department name", required: false },
        ]) || {};
        const res = await api("/api/admin/bootstrap-structure", { method: "POST", body: JSON.stringify(payload) });
        showToast(res.message || "Institution structure ready");
        await renderAdminOverview();
      },
    },
  ]);
}

async function renderHodActions() {
  setActionButtons([
    {
      label: "Department Analytics",
      run: async () => {
        clearContent();
        const [analytics, lecturers, riskCourses] = await Promise.all([
          api("/api/hod/department-analytics"),
          api("/api/hod/lecturers"),
          api("/api/hod/high-risk-courses"),
        ]);

        const summary = makeCard("Department Performance");
        summary.appendChild(
          metricGrid([
            { label: "Average Score", value: analytics.data.average_score },
            { label: "Pass Rate %", value: analytics.data.pass_rate },
            { label: "High-Risk Courses", value: (analytics.data.high_risk_courses || []).length },
            { label: "Lecturers", value: (lecturers.data || []).length },
          ])
        );
        contentGrid.appendChild(summary);

        const lCard = makeCard("Lecturers");
        lCard.appendChild(
          table(
            [
              { key: "staff_id", label: "ID" },
              { key: "full_name", label: "Name" },
              { key: "email", label: "Email" },
            ],
            lecturers.data || []
          )
        );
        contentGrid.appendChild(lCard);

        const hrCard = makeCard("High-Risk Courses");
        hrCard.appendChild(
          table(
            [
              { key: "course_code", label: "Course" },
              { key: "average_score", label: "Average Score" },
            ],
            riskCourses.data || []
          )
        );
        contentGrid.appendChild(hrCard);
      },
    },
  ]);
}

async function renderAdvisorActions() {
  setActionButtons([
    {
      label: "Advisory Dashboard",
      run: async () => {
        clearContent();
        const [studentsRes, riskRes] = await Promise.all([api("/api/advisor/students"), api("/api/advisor/at-risk")]);
        const students = studentsRes.data || [];
        const risks = riskRes.data || [];

        const summary = makeCard("Advisor Summary");
        summary.appendChild(
          metricGrid([
            { label: "Assigned Students", value: students.length },
            { label: "At-Risk", value: risks.length },
          ])
        );
        contentGrid.appendChild(summary);

        const studentsCard = makeCard("Assigned Students");
        studentsCard.appendChild(
          table(
            [
              { key: "matric_no", label: "Matric No" },
              { key: "full_name", label: "Name" },
              { key: "level", label: "Level" },
            ],
            students
          )
        );
        contentGrid.appendChild(studentsCard);
      },
    },
  ]);
}

function renderUploadForm() {
  const card = makeCard("Upload Result CSV", "Format: matric_no, course_code, ca_score, exam_score");
  const form = document.createElement("form");
  form.className = "grid-form";
  form.innerHTML = `
    <label>Session <input type="text" name="session" placeholder="2025/2026" required></label>
    <label>Semester <input type="text" name="semester" placeholder="FIRST" required></label>
    <label>CSV file <input type="file" name="file" accept=".csv" required></label>
    <button type="submit">Upload</button>
  `;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = new FormData(form);
    const res = await api("/api/lecturer/upload-results", { method: "POST", body: payload });
    showToast(res.message || "Upload complete");
    const resultCard = makeCard("Upload Summary");
    resultCard.appendChild(
      metricGrid([
        { label: "Processed", value: res.data.processed },
        { label: "Enrollments Created", value: res.data.created_enrollments },
        { label: "Errors", value: (res.data.errors || []).length },
      ])
    );
    if ((res.data.errors || []).length) {
      resultCard.appendChild(
        table(
          [
            { key: "row", label: "Row" },
            { key: "error", label: "Error" },
          ],
          res.data.errors
        )
      );
    }
    contentGrid.appendChild(resultCard);
  });
  card.appendChild(form);
  return card;
}

async function renderLecturerActions() {
  setActionButtons([
    {
      label: "Class Dashboard",
      run: async () => {
        clearContent();
        const res = await api("/api/lecturer/class-analytics");
        const rows = res.data || [];
        const summary = makeCard("Class Summary");
        summary.appendChild(
          metricGrid([
            { label: "Courses", value: rows.length },
            { label: "Total Records", value: rows.reduce((a, b) => a + (b.records || 0), 0) },
            { label: "At-Risk Students", value: rows.reduce((a, b) => a + (b.at_risk_students || 0), 0) },
          ])
        );
        contentGrid.appendChild(summary);
        const tableCard = makeCard("Course Analytics");
        tableCard.appendChild(
          table(
            [
              { key: "course_code", label: "Course" },
              { key: "course_title", label: "Title" },
              { key: "records", label: "Records" },
              { key: "pass_rate", label: "Pass Rate %" },
              { key: "at_risk_students", label: "At-Risk" },
            ],
            rows
          )
        );
        contentGrid.appendChild(tableCard);
      },
    },
    {
      label: "Upload Results",
      run: async () => {
        clearContent();
        contentGrid.appendChild(renderUploadForm());
      },
    },
  ]);
}

async function renderStudentActions() {
  setActionButtons([
    {
      label: "My Dashboard",
      run: async () => {
        clearContent();
        const [dashRes, coursesRes] = await Promise.all([
          api("/api/student/dashboard"),
          api("/api/student/courses"),
        ]);
        const d = dashRes.data;

        const summary = makeCard("Student Overview");
        summary.appendChild(
          metricGrid([
            { label: "Matric No", value: d.student_info.matric_no },
            { label: "Level", value: d.student_info.level },
            { label: "GPA Estimate", value: d.GPA_estimate ?? 0 },
            { label: "Risk Level", value: d.risk_level || "N/A" },
            { label: "Engagement %", value: d.engagement_index ?? 0 },
          ])
        );
        contentGrid.appendChild(summary);

        const predictive = makeCard("Predictive Learning Insight");
        predictive.appendChild(document.createTextNode(d.predicted_outcome || "Insufficient data"));
        predictive.appendChild(document.createElement("br"));
        predictive.appendChild(statusPill(`LOW: ${d.risk_breakdown?.LOW ?? 0}`));
        predictive.appendChild(statusPill(`MEDIUM: ${d.risk_breakdown?.MEDIUM ?? 0}`));
        predictive.appendChild(statusPill(`HIGH: ${d.risk_breakdown?.HIGH ?? 0}`));
        contentGrid.appendChild(predictive);

        const rec = makeCard("Recommendation");
        rec.appendChild(document.createTextNode(d.recommendation || "No recommendation yet."));
        contentGrid.appendChild(rec);

        const coursesCard = makeCard("Enrolled Courses");
        coursesCard.appendChild(
          table(
            [
              { key: "course_code", label: "Code" },
              { key: "course_title", label: "Course Title" },
              { key: "credit_units", label: "Units" },
              { key: "session", label: "Session" },
              { key: "semester", label: "Semester" },
            ],
            coursesRes.data || []
          )
        );
        contentGrid.appendChild(coursesCard);

        const scoresCard = makeCard("Performance Scores");
        scoresCard.appendChild(
          table(
            [
              { key: "course_code", label: "Course" },
              { key: "ca_score", label: "CA" },
              { key: "exam_score", label: "Exam" },
              { key: "total_score", label: "Total" },
            ],
            d.scores || []
          )
        );
        contentGrid.appendChild(scoresCard);

        const trendCard = makeCard("Performance Trend by Session");
        trendCard.appendChild(
          table(
            [
              { key: "session", label: "Session" },
              { key: "average_score", label: "Average Score" },
            ],
            d.performance_trend || []
          )
        );
        contentGrid.appendChild(trendCard);

        const weaknessCard = makeCard("Weak Learning Areas");
        weaknessCard.appendChild(
          table(
            [
              { key: "course_code", label: "Course" },
              { key: "course_title", label: "Title" },
              { key: "total_score", label: "Score" },
              { key: "status", label: "Status" },
            ],
            d.weak_courses || []
          )
        );
        contentGrid.appendChild(weaknessCard);

        const strengthCard = makeCard("Strength Areas");
        strengthCard.appendChild(
          table(
            [
              { key: "course_code", label: "Course" },
              { key: "course_title", label: "Title" },
              { key: "total_score", label: "Score" },
            ],
            d.strength_courses || []
          )
        );
        contentGrid.appendChild(strengthCard);
      },
    },
    {
      label: "Personalized Plan",
      run: async () => {
        clearContent();
        const res = await api("/api/student/personalized-learning");
        const data = res.data;

        const planCard = makeCard("Weekly Personalized Study Plan");
        planCard.appendChild(
          metricGrid([
            { label: "Target Hours / Week", value: data.personalized_study_plan?.weekly_target_hours ?? 0 },
            { label: "Weak Courses", value: (data.weak_courses || []).length },
            { label: "Strong Courses", value: (data.strength_courses || []).length },
          ])
        );
        contentGrid.appendChild(planCard);

        const scheduleCard = makeCard("Study Timetable");
        scheduleCard.appendChild(
          table(
            [
              { key: "day", label: "Day" },
              { key: "focus", label: "Learning Focus" },
              { key: "hours", label: "Hours" },
            ],
            data.personalized_study_plan?.weekly_schedule || []
          )
        );
        contentGrid.appendChild(scheduleCard);

        const interventionCard = makeCard("Intervention Recommendations");
        interventionCard.appendChild(list(data.intervention_recommendations || []));
        contentGrid.appendChild(interventionCard);

        const actionsCard = makeCard("Next Learning Actions");
        actionsCard.appendChild(list(data.next_actions || []));
        contentGrid.appendChild(actionsCard);
      },
    },
    {
      label: "Download Report",
      run: async () => {
        clearContent();
        const panel = makeCard("Export Personalized Learning Report");
        const controls = document.createElement("div");
        controls.className = "actions";
        const csvBtn = document.createElement("button");
        csvBtn.textContent = "Download CSV";
        csvBtn.onclick = async () => {
          await downloadFile("/api/student/personalized-learning-report?format=csv", "personalized_report.csv");
          showToast("CSV report downloaded");
        };
        const pdfBtn = document.createElement("button");
        pdfBtn.className = "ghost-btn";
        pdfBtn.textContent = "Download PDF";
        pdfBtn.onclick = async () => {
          await downloadFile("/api/student/personalized-learning-report?format=pdf", "personalized_report.pdf");
          showToast("PDF report downloaded");
        };
        controls.appendChild(csvBtn);
        controls.appendChild(pdfBtn);
        panel.appendChild(controls);
        contentGrid.appendChild(panel);
      },
    },
  ]);
}

async function renderActionsByRole() {
  if (state.role === "ADMIN") return renderAdminActions();
  if (state.role === "HOD") return renderHodActions();
  if (state.role === "COURSE_ADVISOR") return renderAdvisorActions();
  if (state.role === "LECTURER") return renderLecturerActions();
  if (state.role === "STUDENT") return renderStudentActions();
  clearContent();
  contentGrid.appendChild(makeCard("Info", `Unsupported role: ${state.role}`));
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const universityId = document.getElementById("universityId").value;
  const identifier = document.getElementById("identifier").value.trim();
  const password = document.getElementById("password").value.trim();
  if (!universityId) {
    showToast("Select your university first", true);
    return;
  }
  try {
    await login(identifier, password, universityId);
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearSession();
  actionsEl.innerHTML = "";
  clearContent();
  renderApp();
  showToast("Logged out");
});

window.addEventListener("load", async () => {
  await loadUniversityOptions();
  try {
    if (state.token) {
      const me = await api("/api/auth/me");
      state.role = me.data.role;
      const uni = state.universities.find((u) => u.university_id === me.data.university_id);
      state.user = {
        id: me.data.id,
        name: me.data.full_name,
        role: me.data.role,
        university_id: me.data.university_id,
        university_name: uni ? uni.name : "",
      };
      persistSession();
    }
  } catch {
    clearSession();
  }
  renderApp();
});
