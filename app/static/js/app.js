/**
 * Smart Campus Facility Issue Prediction & Prioritization System
 * Master Client Application Controller
 * Version 2.0 - Role-Based Access Control, CSV Dataset Management & AI Triage
 */

class SmartCampusApp {
  constructor() {
    this.currentView = "home";
    this.theme = localStorage.getItem("sc_theme") || "light";
    this.tourStep = 0;
    this.charts = {};
    this.cachedComplaints = [];
    this.adminComplaints = [];
    this.studentComplaints = [];
    this.studentFilter = "All";
    
    // Auth State
    this.authToken = localStorage.getItem("sc_auth_token") || null;
    this.currentUser = JSON.parse(localStorage.getItem("sc_user") || "null");
    this.loginTabRole = "student";

    // Dataset Management & Admin Pagination
    this.adminOffset = 0;
    this.adminLimit = 50;
    this.adminTotal = 5500;
    this.selectedDatasetFile = null;

    // Audit logs
    this.auditLogs = [];

    this.activeWeights = {
      weight_severity: 0.35,
      weight_recurrence: 0.25,
      weight_footfall: 0.20,
      weight_location_risk: 0.10,
      weight_impact: 0.10
    };
    this.lastAnalyzedRecord = null;

    // 5-Minute Walkthrough Tour (Updated for Two Roles)
    this.tourSteps = [
      {
        title: "Minute 1: Student Persona & Clean Portal Overview",
        badge: "Step 1 of 5 (0:00 - 1:00)",
        view: "student-home",
        content: `
          <h4 style="font-size:1rem; font-weight:700; margin-bottom:8px;">Persona 1: Enrolled Student Portal</h4>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            The Student Portal provides an <strong>isolated, non-technical interface</strong>. Students see only their own reported defects, active repair progression, and campus emergency hotlines.
          </p>
          <div style="background:var(--bg-card-subtle); padding:10px 12px; border-radius:6px; font-size:0.82rem; margin-bottom:10px;">
            🔒 <strong>Strict Privacy Isolation:</strong> Students can never view other students' tickets, administrator control panels, ML weights, or raw datasets.
          </div>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6;">
            Notice the personal KPI cards showing tickets reported by Rahul Sharma (Computer Science & Engineering).
          </p>
        `
      },
      {
        title: "Minute 2: Student Submits Complaint with Automated AI Triage",
        badge: "Step 2 of 5 (1:00 - 2:00)",
        view: "student-submit",
        content: `
          <h4 style="font-size:1rem; font-weight:700; margin-bottom:8px;">Zero-Friction Facility Intake</h4>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            Students describe issues in natural language. Notice there are <strong>NO priority or severity dropdowns</strong> in this form!
          </p>
          <div style="background:var(--primary-light); border:1px solid var(--primary-border); padding:10px 12px; border-radius:6px; font-size:0.82rem; margin-bottom:12px;">
            ⚡ <strong>Automated AI Prioritization:</strong> Our pipeline automatically extracts linguistic urgency, maps location footfall density, and calculates priority without burdening students.
          </div>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6;">
            Upon submission, students receive a tracking ticket with a <strong>4-step status stepper</strong> (Submitted → Open → In Progress → Resolved).
          </p>
        `
      },
      {
        title: "Minute 3: Administrator Login & Executive Overview (5,500 Records)",
        badge: "Step 3 of 5 (2:00 - 3:00)",
        view: "dashboard",
        content: `
          <h4 style="font-size:1rem; font-weight:700; margin-bottom:8px;">Persona 2: Campus Facility Administrator</h4>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            Campus Directors and Maintenance Managers log in with administrative credentials to access all operations.
          </p>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            All dashboard statistics, KPI cards, and charts are calculated dynamically from the <strong>complete 5,500-record historical campus dataset</strong>.
          </p>
          <div style="background:var(--bg-card-subtle); padding:10px 12px; border-radius:6px; font-size:0.82rem;">
            📊 Real-time metrics track open vs. resolved complaints, high-priority issues, and high-footfall chronic hotspots across all campus zones.
          </div>
        `
      },
      {
        title: "Minute 4: Priority Queue & Dispatch Operations",
        badge: "Step 4 of 5 (3:00 - 4:00)",
        view: "priority-queue",
        content: `
          <h4 style="font-size:1rem; font-weight:700; margin-bottom:8px;">Mathematically Prioritized Dispatch</h4>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            Supervisors manage work orders strictly sorted by computed Priority Score (0-100). High-severity failures in high-footfall areas immediately rise to the top.
          </p>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            Admins can update ticket statuses between <strong>Open, In Progress, and Resolved</strong>, assign technicians, or click <strong>'Why?'</strong> to view game-theoretic SHAP explainability breakdowns.
          </p>
        `
      },
      {
        title: "Minute 5: Risk Intel, Dataset Management & Model Metrics",
        badge: "Step 5 of 5 (4:00 - 5:00)",
        view: "dataset-management",
        content: `
          <h4 style="font-size:1rem; font-weight:700; margin-bottom:8px;">Dataset Management & Auditing</h4>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6; margin-bottom:12px;">
            Under <strong>Data & ML</strong>, administrators can:
          </p>
          <ul style="color:var(--text-muted); font-size:0.85rem; line-height:1.6; margin-left:18px; margin-bottom:12px;">
            <li>Inspect the 5,500 dataset summary (columns, missing values, duplicates)</li>
            <li>Preview raw records with sticky schema headers</li>
            <li>Upload replacement CSV datasets with mandatory column schema validation</li>
            <li>Export datasets and restore the pristine 5,500 baseline</li>
          </ul>
          <p style="color:var(--text-muted); font-size:0.88rem; line-height:1.6;">
            Together, these modules provide complete transparency, enterprise data governance, and predictive maintenance efficiency.
          </p>
        `
      }
    ];

    this.init();
  }

  async init() {
    this.applyTheme(this.theme);
    this.setupNavigation();
    this.setupForms();
    this.setupModals();
    this.setupFilters();

    // Initialize or restore session
    if (!this.currentUser) {
      // Default to Rahul Sharma (Student) for instant preview
      await this.quickLogin("STU101", "student123", false);
    } else {
      this.applyRoleState();
    }
  }

  // --- Theme Management ---
  applyTheme(theme) {
    this.theme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("sc_theme", theme);

    const sunIcon = document.getElementById("sunIcon");
    const moonIcon = document.getElementById("moonIcon");
    if (sunIcon && moonIcon) {
      if (theme === "dark") {
        sunIcon.style.display = "none";
        moonIcon.style.display = "block";
      } else {
        sunIcon.style.display = "block";
        moonIcon.style.display = "none";
      }
    }

    if (Object.keys(this.charts).length > 0) {
      this.renderCharts();
    }
  }

  toggleTheme() {
    const nextTheme = this.theme === "light" ? "dark" : "light";
    this.applyTheme(nextTheme);
    this.showToast(`Switched to ${nextTheme === "dark" ? "Dark" : "Light"} Mode`);
  }

  // --- Authentication & Session Management ---
  setLoginTab(role) {
    this.loginTabRole = role;
    const tabStudent = document.getElementById("tabStudent");
    const tabAdmin = document.getElementById("tabAdmin");
    const userLabel = document.getElementById("loginUserLabel");
    const userInput = document.getElementById("loginUsername");

    if (role === "student") {
      tabStudent.classList.add("active");
      tabAdmin.classList.remove("active");
      userLabel.innerText = "Student ID or Campus Email";
      userInput.placeholder = "e.g. STU101 or rahul.sharma@campus.edu";
    } else {
      tabAdmin.classList.add("active");
      tabStudent.classList.remove("active");
      userLabel.innerText = "Administrator ID or Official Email";
      userInput.placeholder = "e.g. ADMIN01 or admin.facilities@campus.edu";
    }
  }

  async handleLogin() {
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;
    await this.login(username, password);
  }

  async quickLogin(username, password, notify = true) {
    const userInput = document.getElementById("loginUsername");
    const passInput = document.getElementById("loginPassword");
    if (userInput) userInput.value = username;
    if (passInput) passInput.value = password;

    await this.login(username, password, notify);
  }

  async login(username, password, notify = true) {
    const errBox = document.getElementById("loginErrorMsg");
    if (errBox) errBox.style.display = "none";

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        if (errBox) {
          errBox.innerText = data.detail || "Authentication failed. Please verify credentials.";
          errBox.style.display = "block";
        }
        return;
      }

      this.authToken = data.token;
      this.currentUser = data.user;
      localStorage.setItem("sc_auth_token", this.authToken);
      localStorage.setItem("sc_user", JSON.stringify(this.currentUser));

      if (notify) {
        this.showToast(data.message || "Signed in successfully!");
      }

      this.applyRoleState();
    } catch (err) {
      console.error(err);
      if (errBox) {
        errBox.innerText = "Network error communicating with authentication service.";
        errBox.style.display = "block";
      }
    }
  }

  showLoginView() {
    this.navigateTo("login");
  }

  logout() {
    this.authToken = null;
    this.currentUser = null;
    localStorage.removeItem("sc_auth_token");
    localStorage.removeItem("sc_user");
    this.showToast("Signed out successfully.");
    this.showLoginView();
  }

  applyRoleState() {
    if (!this.currentUser) {
      this.showLoginView();
      return;
    }

    const user = this.currentUser;
    const isStudent = user.role === "student";

    // Update Header User Badge
    const headerName = document.getElementById("headerUserName");
    const headerRole = document.getElementById("headerUserRole");
    const weightsBtn = document.getElementById("weightsModalBtn");

    if (headerName) headerName.innerText = user.name;
    if (headerRole) {
      headerRole.innerText = isStudent ? "Student" : "Admin";
      headerRole.className = `user-role-tag role-${user.role}`;
    }

    // Toggle navigation groups
    const stuNav = document.getElementById("studentNavGroup");
    const adminNav = document.getElementById("adminNavGroup");

    if (stuNav) stuNav.style.display = isStudent ? "block" : "none";
    if (adminNav) adminNav.style.display = isStudent ? "none" : "block";
    if (weightsBtn) weightsBtn.style.display = isStudent ? "none" : "inline-flex";

    // Route to appropriate home
    if (isStudent) {
      this.loadStudentComplaints();
      this.loadStudentProfile();
      this.navigateTo("student-home");
    } else {
      this.loadKPIs();
      this.loadQueue();
      this.loadRiskMatrix();
      this.loadRecurringData();
      this.loadForecasts();
      this.loadCampusMap();
      this.loadModelMetrics();
      this.loadWeights();
      this.loadAdminComplaints();
      this.loadDatasetSummary();
      this.loadAuditLogs();
      this.navigateTo("dashboard");
    }
  }

  async fetchWithAuth(url, options = {}) {
    const headers = options.headers || {};
    if (this.authToken) {
      headers["Authorization"] = `Bearer ${this.authToken}`;
    }
    options.headers = headers;

    const res = await fetch(url, options);
    if (res.status === 401) {
      this.logout();
      throw new Error("Unauthorized");
    }
    return res;
  }

  // --- Navigation & Routing ---
  setupNavigation() {
    document.querySelectorAll(".sidebar-nav").forEach(nav => {
      nav.addEventListener("click", (e) => {
        const item = e.target.closest(".nav-item");
        if (item) {
          const viewId = item.getAttribute("data-view");
          this.navigateTo(viewId);
        }
      });
    });

    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) themeBtn.addEventListener("click", () => this.toggleTheme());

    const mobBtn = document.getElementById("mobileMenuToggle");
    if (mobBtn) mobBtn.addEventListener("click", () => {
      document.getElementById("appSidebar").classList.toggle("mobile-open");
    });

    const resetBtn = document.getElementById("resetDemoBtn");
    if (resetBtn) resetBtn.addEventListener("click", () => this.confirmResetDataset());
  }

  navigateTo(viewId) {
    this.currentView = viewId;

    // Update active class on nav items
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
      if (item.getAttribute("data-view") === viewId) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });

    // Update view visibility
    document.querySelectorAll(".app-view").forEach(view => {
      view.classList.remove("active");
    });
    const target = document.getElementById(`view-${viewId}`);
    if (target) {
      target.classList.add("active");
    }

    // Update header titles
    const titles = {
      "login": { title: "Portal Authentication", sub: "Sign in as Student or Facility Administrator" },
      "student-home": { title: "Student Facility Services", sub: "Report maintenance defects and track repair progress" },
      "student-submit": { title: "Fast-Track Facility Intake", sub: "AI automatically prioritizes and routes your repair request" },
      "student-complaints": { title: "My Reported Issues", sub: "Real-time repair tracking and lifecycle progression" },
      "student-help": { title: "Student Facilities Help & SLA", sub: "Campus service levels and 24/7 emergency hotlines" },
      "student-profile": { title: "Student Identity Profile", sub: "Account details and reported ticket metrics" },
      "home": { title: "Smart Campus Maintenance Intelligence", sub: "Predictive facility triage, recurrence tracking, and explainable prioritization" },
      "how-it-works": { title: "How It Works (5-Step Visual Workflow)", sub: "Transparent end-to-end pipeline from complaint to maintenance action" },
      "submit-complaint": { title: "Student & Staff Facility Complaint Submission", sub: "Submit a facility defect and view instant real-time AI prioritization" },
      "ai-pipeline": { title: "AI Analysis & Decision Pipeline Sandbox", sub: "Interactive pipeline debugger testing all 7 processing stages live" },
      "dashboard": { title: "Maintenance Operations Dashboard", sub: "Campus-wide facility health KPIs, issue distribution, and trendlines" },
      "admin-complaints": { title: "Campus Facilities Complaint Directory", sub: "Comprehensive master list of all 5,500 historical and live campus reports" },
      "priority-queue": { title: "Intelligent Maintenance Priority Queue", sub: "Work orders prioritized by computed urgency, recurrence, and footfall" },
      "risk-intelligence": { title: "Campus Facility Risk Intelligence", sub: "Campus location vulnerability rankings and chronic hazard hotspots" },
      "recurring-issues": { title: "Chronic Recurring Problem Tracking", sub: "Root-cause tracking for repeated facility failures (Block C Case Study)" },
      "predictive-maintenance": { title: "Predictive Issue-Risk Forecasting", sub: "Upcoming 7-30 day risk windows based on historical recurrence cycles" },
      "campus-map": { title: "Campus Location & Hotspot Map", sub: "Interactive spatial map displaying building risk and footfall load" },
      "dataset-management": { title: "Dataset Management & Ingestion", sub: "Summary metrics, schema validation, CSV ingestion & export" },
      "explainable-ai": { title: "Explainable AI (SHAP Waterfall Breakdown)", sub: "Exact mathematical feature attributions explaining model decisions" },
      "ml-architecture": { title: "Technology Stack & Genuine ML Metrics", sub: "Production architecture and Scikit-learn holdout evaluation results" },
      "admin-users": { title: "Campus User Directory & Access Roles", sub: "Active registered student and administrative personas" },
      "audit-logs": { title: "System Security & Audit Activity Logs", sub: "Immutable log stream of ticket submissions and triage actions" }
    };

    if (titles[viewId]) {
      const titleEl = document.getElementById("currentViewTitle");
      const subEl = document.getElementById("currentViewSubtitle");
      if (titleEl) titleEl.innerText = titles[viewId].title;
      if (subEl) subEl.innerText = titles[viewId].sub;
    }

    if (viewId === "dashboard") {
      this.renderCharts();
    }
    if (viewId === "student-home" || viewId === "student-complaints") {
      this.loadStudentComplaints();
    }
    if (viewId === "admin-complaints") {
      this.loadAdminComplaints();
    }
    if (viewId === "dataset-management") {
      this.loadDatasetSummary();
    }

    // Scroll to top
    const viewArea = document.querySelector(".view-content-area");
    if (viewArea) viewArea.scrollTop = 0;

    const sidebar = document.getElementById("appSidebar");
    if (sidebar) sidebar.classList.remove("mobile-open");
  }

  // --- Student Portal Implementation ---
  async loadStudentComplaints() {
    if (!this.currentUser || this.currentUser.role !== "student") return;

    try {
      const res = await this.fetchWithAuth("/api/student/complaints");
      const data = await res.json();
      this.studentComplaints = data.complaints || [];

      // Update Student KPIs
      const total = this.studentComplaints.length;
      const open = this.studentComplaints.filter(c => c.status === "Open" || c.status === "Pending").length;
      const prog = this.studentComplaints.filter(c => c.status === "In Progress").length;
      const resCount = this.studentComplaints.filter(c => c.status === "Resolved").length;

      const kpiTot = document.getElementById("stuKpiTotal");
      const kpiOp = document.getElementById("stuKpiOpen");
      const kpiPr = document.getElementById("stuKpiInProgress");
      const kpiRs = document.getElementById("stuKpiResolved");

      if (kpiTot) kpiTot.innerText = total;
      if (kpiOp) kpiOp.innerText = open;
      if (kpiPr) kpiPr.innerText = prog;
      if (kpiRs) kpiRs.innerText = resCount;

      const cntAll = document.getElementById("stuCountAll");
      const cntOp = document.getElementById("stuCountOpen");
      const cntPr = document.getElementById("stuCountProg");
      const cntRs = document.getElementById("stuCountRes");

      if (cntAll) cntAll.innerText = total;
      if (cntOp) cntOp.innerText = open;
      if (cntPr) cntPr.innerText = prog;
      if (cntRs) cntRs.innerText = resCount;

      this.renderStudentComplaintsTable();
      this.renderStudentHomeRecentList();
    } catch (err) {
      console.error(err);
    }
  }

  renderStudentComplaintsTable() {
    const tbody = document.getElementById("studentComplaintsTableBody");
    if (!tbody) return;

    let records = this.studentComplaints;
    if (this.studentFilter !== "All") {
      records = records.filter(c => c.status === this.studentFilter);
    }

    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 28px; color: var(--text-muted);">No complaints found for filter "${this.studentFilter}".</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    records.forEach(c => {
      const tr = document.createElement("tr");
      const pri = c.priority || "Medium";
      const statusBadge = c.status === "Resolved" ? "low" : (c.status === "In Progress" ? "inprogress" : "open");

      tr.innerHTML = `
        <td><strong>${c.complaint_id || c.id}</strong></td>
        <td>${c.facility_type}</td>
        <td>${c.location}</td>
        <td style="max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${c.complaint_text || c.description}">
          ${c.complaint_text || c.description}
        </td>
        <td style="font-size:0.78rem; color:var(--text-muted);">${c.timestamp || "Recent"}</td>
        <td><span class="badge badge-${statusBadge}">${c.status}</span></td>
        <td><span class="badge badge-${pri.toLowerCase()}">${pri} Priority</span></td>
        <td>
          <button class="btn btn-outline" style="padding:3px 8px; font-size:0.75rem;" onclick="app.openStudentProgressModal('${c.complaint_id || c.id}')">
            Track Status
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  renderStudentHomeRecentList() {
    const tbody = document.getElementById("studentHomeRecentList");
    if (!tbody) return;

    const recent = this.studentComplaints.slice(0, 5);
    if (recent.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 20px; color: var(--text-muted);">You have not reported any issues yet. Click 'Report a New Issue' to start.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    recent.forEach(c => {
      const tr = document.createElement("tr");
      const statusBadge = c.status === "Resolved" ? "low" : (c.status === "In Progress" ? "inprogress" : "open");
      const pri = c.priority || "Medium";

      tr.innerHTML = `
        <td><strong>${c.complaint_id || c.id}</strong></td>
        <td>${c.facility_type}</td>
        <td>${c.location}</td>
        <td style="font-size:0.78rem; color:var(--text-muted);">${c.timestamp || "Recent"}</td>
        <td><span class="badge badge-${statusBadge}">${c.status}</span></td>
        <td><span class="badge badge-${pri.toLowerCase()}">${pri}</span></td>
        <td>
          <button class="btn btn-outline" style="padding:2px 6px; font-size:0.72rem;" onclick="app.openStudentProgressModal('${c.complaint_id || c.id}')">
            View
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  filterStudentComplaints(status) {
    this.studentFilter = status;
    const nav = document.getElementById("stuFilterTabs");
    if (nav) {
      nav.querySelectorAll(".tab-btn").forEach(btn => {
        if (btn.innerText.includes(status)) {
          btn.classList.add("active");
        } else {
          btn.classList.remove("active");
        }
      });
    }
    this.renderStudentComplaintsTable();
  }

  prefillStudentScenario(type) {
    const scenarios = {
      "water_cooler": {
        facility: "Water Cooler",
        location: "Block C (Science & Labs)",
        desc: "The drinking water cooler on Block C 2nd floor has stopped dispensing cold water and is leaking onto the corridor floor."
      },
      "washroom_tap": {
        facility: "Washroom & Plumbing",
        location: "Central Cafeteria & Food Court",
        desc: "Washroom basin tap near Cafeteria queue is broken and water is continuously flooding the washroom threshold."
      },
      "library_light": {
        facility: "Lighting & Electrical",
        location: "Central Library",
        desc: "Tube lights on the 3rd floor quiet reading room are flickering constantly and creating a humming noise."
      }
    };
    const s = scenarios[type];
    if (s) {
      document.getElementById("stuSubmitFacility").value = s.facility;
      document.getElementById("stuSubmitLocation").value = s.location;
      document.getElementById("stuSubmitDesc").value = s.desc;
    }
  }

  async handleStudentSubmit() {
    const desc = document.getElementById("stuSubmitDesc").value.trim();
    const facility = document.getElementById("stuSubmitFacility").value;
    const location = document.getElementById("stuSubmitLocation").value;

    const payload = {
      reporter_name: this.currentUser.name,
      reporter_role: "Student",
      student_id: this.currentUser.id,
      facility_type: facility,
      location: location,
      description: desc
    };

    try {
      const res = await this.fetchWithAuth("/api/student/complaints/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        this.showToast(`Complaint filed! Ticket ID: ${data.ticket_number}`);
        document.getElementById("stuSubmitDesc").value = "";
        await this.loadStudentComplaints();
        this.navigateTo("student-complaints");
        this.openStudentProgressModal(data.ticket_number);
      } else {
        this.showToast("Failed to file complaint.", "error");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Network error submitting complaint.", "error");
    }
  }

  openStudentProgressModal(complaintId) {
    const rec = this.studentComplaints.find(c => c.complaint_id === complaintId || c.id === complaintId);
    if (!rec) {
      this.showToast("Complaint ticket details not found.", "error");
      return;
    }

    const modal = document.getElementById("studentProgressModal");
    modal.classList.add("active");

    document.getElementById("stuMdlTicketId").innerText = rec.complaint_id || rec.id;
    document.getElementById("stuMdlFacility").innerText = rec.facility_type || rec.facility_category;
    document.getElementById("stuMdlLocation").innerText = rec.location || rec.building_name;
    document.getElementById("stuMdlTech").innerText = rec.technician_assigned || "Pending Dispatch";
    document.getElementById("stuMdlDesc").innerText = rec.complaint_text || rec.description;

    const pri = rec.priority || "Medium";
    document.getElementById("stuMdlPriority").innerHTML = `<span class="badge badge-${pri.toLowerCase()}">${pri} Priority</span>`;

    // Stepper logic
    const s1 = document.getElementById("step1");
    const s2 = document.getElementById("step2");
    const s3 = document.getElementById("step3");
    const s4 = document.getElementById("step4");

    [s1, s2, s3, s4].forEach(s => {
      s.className = "stepper-step";
    });

    const status = rec.status;
    if (status === "Resolved") {
      s1.classList.add("completed");
      s2.classList.add("completed");
      s3.classList.add("completed");
      s4.classList.add("completed");
    } else if (status === "In Progress") {
      s1.classList.add("completed");
      s2.classList.add("completed");
      s3.classList.add("active");
    } else if (status === "Open" || status === "Pending") {
      s1.classList.add("completed");
      s2.classList.add("active");
    } else {
      s1.classList.add("active");
    }
  }

  closeStudentProgressModal() {
    const modal = document.getElementById("studentProgressModal");
    if (modal) modal.classList.remove("active");
  }

  loadStudentProfile() {
    if (!this.currentUser) return;
    const u = this.currentUser;

    const pName = document.getElementById("profileName");
    const pEmail = document.getElementById("profileEmail");
    const pDept = document.getElementById("profileDept");
    const pIdBadge = document.getElementById("profileIdBadge");
    const pComplaints = document.getElementById("profileComplaintsCount");
    const pActive = document.getElementById("profileActiveCount");
    const pAvatar = document.getElementById("profileAvatarText");

    const initials = u.name.split(" ").map(n => n[0]).join("");
    if (pAvatar) pAvatar.innerText = initials;
    if (pName) pName.innerText = u.name;
    if (pEmail) pEmail.innerText = u.email;
    if (pDept) pDept.innerText = u.department;
    if (pIdBadge) pIdBadge.innerText = `ID: ${u.id}`;
    if (pComplaints) pComplaints.innerText = this.studentComplaints.length;
    if (pActive) pActive.innerText = this.studentComplaints.filter(c => c.status !== "Resolved").length;

    const stuSubName = document.getElementById("stuSubmitName");
    const stuSubId = document.getElementById("stuSubmitId");
    if (stuSubName) stuSubName.value = u.name;
    if (stuSubId) stuSubId.value = u.id;

    const welcomeTitle = document.getElementById("studentWelcomeTitle");
    const welcomeBadge = document.getElementById("studentWelcomeBadge");
    if (welcomeTitle) welcomeTitle.innerText = `Welcome Back, ${u.name.split(" ")[0]}!`;
    if (welcomeBadge) welcomeBadge.innerText = `Student Portal • ${u.department}`;
  }

  // --- Administrator Complaints Management (5,500 records) ---
  async loadAdminComplaints() {
    const search = document.getElementById("adminSearchInput")?.value?.trim() || "";
    const cat = document.getElementById("adminFilterCategory")?.value || "All";
    const sev = document.getElementById("adminFilterSeverity")?.value || "All";
    const pri = document.getElementById("adminFilterPriority")?.value || "All";
    const stat = document.getElementById("adminFilterStatus")?.value || "All";

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (cat !== "All") params.append("facility_type", cat);
    if (sev !== "All") params.append("severity", sev);
    if (pri !== "All") params.append("priority", pri);
    if (stat !== "All") params.append("status", stat);
    params.append("limit", this.adminLimit);
    params.append("offset", this.adminOffset);

    try {
      const res = await this.fetchWithAuth(`/api/admin/complaints?${params.toString()}`);
      const data = await res.json();
      this.adminComplaints = data.records || [];
      this.adminTotal = data.total || 0;

      this.renderAdminComplaintsTable();
    } catch (err) {
      console.error(err);
    }
  }

  renderAdminComplaintsTable() {
    const tbody = document.getElementById("adminComplaintsTableBody");
    if (!tbody) return;

    if (this.adminComplaints.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 24px; color: var(--text-muted);">No records matched the selected filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    this.adminComplaints.forEach(c => {
      const tr = document.createElement("tr");
      const pri = c.priority || "Medium";
      const statusBadge = c.status === "Resolved" ? "low" : (c.status === "In Progress" ? "inprogress" : "open");

      tr.innerHTML = `
        <td><strong>${c.complaint_id || c.id}</strong></td>
        <td>
          <div>${c.reporter_name || "Student"}</div>
          <span style="font-size:0.7rem; color:var(--text-muted);">${c.student_id || ""}</span>
        </td>
        <td>${c.facility_type || c.facility_category}</td>
        <td>${c.location || c.building_name}</td>
        <td><span class="badge badge-${(c.severity || "Medium").toLowerCase()}">${c.severity || "Medium"}</span></td>
        <td>
          <strong style="color:var(--primary); font-size:0.9rem;">${Number(c.priority_score || 50).toFixed(1)}</strong>
          <span style="font-size:0.7rem; color:var(--text-muted);">(${pri})</span>
        </td>
        <td><span class="badge badge-${statusBadge}">${c.status}</span></td>
        <td style="font-size:0.8rem;">
          <div>${c.technician_assigned || "Pending Dispatch"}</div>
          <span style="font-size:0.7rem; color:var(--text-muted);">${c.department || ""}</span>
        </td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline" style="padding:2px 6px; font-size:0.72rem;" onclick="app.openAdminEditModal('${c.complaint_id || c.id}')" title="Edit status & staff">
              Edit
            </button>
            <button class="btn btn-outline" style="padding:2px 6px; font-size:0.72rem;" onclick="app.openTicketDetail('${c.complaint_id || c.id}')" title="SHAP Explainability">
              Why?
            </button>
            <button class="btn btn-outline" style="padding:2px 6px; font-size:0.72rem; color:var(--risk-critical); border-color:var(--risk-critical);" onclick="app.deleteAdminComplaint('${c.complaint_id || c.id}')" title="Delete record">
              &times;
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Update pagination info
    const info = document.getElementById("adminPaginationInfo");
    const pageNum = document.getElementById("adminCurrentPage");
    if (info) {
      const start = this.adminOffset + 1;
      const end = Math.min(this.adminOffset + this.adminLimit, this.adminTotal);
      info.innerText = `Showing records ${start} - ${end} of ${this.adminTotal.toLocaleString()}`;
    }
    if (pageNum) {
      const curPage = Math.floor(this.adminOffset / this.adminLimit) + 1;
      pageNum.innerText = `Page ${curPage}`;
    }
  }

  filterAdminComplaints() {
    this.adminOffset = 0;
    this.loadAdminComplaints();
  }

  resetAdminFilters() {
    const search = document.getElementById("adminSearchInput");
    const cat = document.getElementById("adminFilterCategory");
    const sev = document.getElementById("adminFilterSeverity");
    const pri = document.getElementById("adminFilterPriority");
    const stat = document.getElementById("adminFilterStatus");

    if (search) search.value = "";
    if (cat) cat.value = "All";
    if (sev) sev.value = "All";
    if (pri) pri.value = "All";
    if (stat) stat.value = "All";

    this.adminOffset = 0;
    this.loadAdminComplaints();
  }

  changeAdminPage(delta) {
    const nextOffset = this.adminOffset + (delta * this.adminLimit);
    if (nextOffset >= 0 && nextOffset < this.adminTotal) {
      this.adminOffset = nextOffset;
      this.loadAdminComplaints();
    }
  }

  openAdminEditModal(complaintId) {
    const rec = this.adminComplaints.find(c => c.complaint_id === complaintId || c.id === complaintId);
    if (!rec) return;

    const modal = document.getElementById("adminEditModal");
    modal.classList.add("active");

    document.getElementById("adminEditComplaintId").value = rec.complaint_id || rec.id;
    document.getElementById("adminEditMdlTicketId").innerText = rec.complaint_id || rec.id;
    document.getElementById("adminEditStatus").value = rec.status || "Open";
    document.getElementById("adminEditDept").value = rec.department || "General Facilities";
    document.getElementById("adminEditTechnician").value = rec.technician_assigned || "";
  }

  closeAdminEditModal() {
    const modal = document.getElementById("adminEditModal");
    if (modal) modal.classList.remove("active");
  }

  async saveAdminComplaintUpdate() {
    const id = document.getElementById("adminEditComplaintId").value;
    const status = document.getElementById("adminEditStatus").value;
    const department = document.getElementById("adminEditDept").value;
    const technician = document.getElementById("adminEditTechnician").value;

    try {
      const res = await this.fetchWithAuth(`/api/admin/complaints/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: status,
          department: department,
          technician_assigned: technician
        })
      });
      const data = await res.json();

      if (data.success) {
        this.showToast(`Complaint ${id} updated successfully!`);
        this.closeAdminEditModal();
        this.loadAdminComplaints();
        this.loadKPIs();
        this.loadQueue();

        // Append to audit log
        this.addAuditEntry("Complaint Updated", this.currentUser.name, `Updated status of ${id} to ${status}`);
      }
    } catch (err) {
      console.error(err);
      this.showToast("Failed to update complaint", "error");
    }
  }

  async deleteAdminComplaint(complaintId) {
    if (!confirm(`Are you sure you want to permanently delete complaint ${complaintId}?`)) return;

    try {
      const res = await this.fetchWithAuth(`/api/admin/complaints/${complaintId}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(`Complaint ${complaintId} deleted.`);
        this.loadAdminComplaints();
        this.loadKPIs();
        this.loadQueue();
        this.addAuditEntry("Complaint Deleted", this.currentUser.name, `Deleted ticket ${complaintId}`);
      }
    } catch (err) {
      console.error(err);
      this.showToast("Failed to delete complaint", "error");
    }
  }

  // --- Dataset Management (Summary, Preview, Upload, Export, Reset) ---
  async loadDatasetSummary() {
    if (!this.currentUser || this.currentUser.role !== "admin") return;

    try {
      const res = await this.fetchWithAuth("/api/admin/dataset/summary");
      const summary = await res.json();

      // Update Summary Cards
      const totRec = document.getElementById("dsTotalRecords");
      const totCol = document.getElementById("dsTotalCols");
      const missCnt = document.getElementById("dsMissingCount");
      const dupCnt = document.getElementById("dsDuplicateCount");

      if (totRec) totRec.innerText = (summary.total_records || 5500).toLocaleString();
      if (totCol) totCol.innerText = summary.total_columns || 21;
      if (missCnt) missCnt.innerText = summary.missing_values_count || 0;
      if (dupCnt) dupCnt.innerText = summary.duplicate_records || 0;

      // Update Facility Dist
      const facList = document.getElementById("datasetFacilityDistList");
      if (facList && summary.facility_distribution) {
        facList.innerHTML = Object.entries(summary.facility_distribution).map(([k, v]) => `
          <div style="display:flex; justify-content:space-between; font-size:0.78rem;">
            <span>${k}</span>
            <strong>${v} (${((v / summary.total_records) * 100).toFixed(1)}%)</strong>
          </div>
        `).join("");
      }

      // Update Severity Dist
      const sevList = document.getElementById("datasetSeverityDistList");
      if (sevList && summary.severity_distribution) {
        sevList.innerHTML = Object.entries(summary.severity_distribution).map(([k, v]) => `
          <div style="display:flex; justify-content:space-between; font-size:0.78rem;">
            <span>${k}</span>
            <strong>${v} (${((v / summary.total_records) * 100).toFixed(1)}%)</strong>
          </div>
        `).join("");
      }

      // Render Preview Table
      this.renderDatasetPreview(summary.preview_rows || []);
    } catch (err) {
      console.error(err);
    }
  }

  renderDatasetPreview(rows) {
    const thead = document.getElementById("datasetPreviewHeader");
    const tbody = document.getElementById("datasetPreviewBody");
    if (!thead || !tbody || rows.length === 0) return;

    const cols = Object.keys(rows[0]);
    thead.innerHTML = cols.map(c => `<th>${c}</th>`).join("");

    tbody.innerHTML = rows.map(r => `
      <tr>
        ${cols.map(c => `<td>${r[c] !== null && r[c] !== undefined ? String(r[c]) : ""}</td>`).join("")}
      </tr>
    `).join("");
  }

  handleDatasetFileSelect(file) {
    if (!file) return;
    this.selectedDatasetFile = file;

    const box = document.getElementById("selectedFileBox");
    const nameEl = document.getElementById("selectedFileName");
    const sizeEl = document.getElementById("selectedFileSize");
    const errBox = document.getElementById("datasetUploadError");

    if (errBox) errBox.style.display = "none";

    if (box && nameEl && sizeEl) {
      nameEl.innerText = file.name;
      sizeEl.innerText = `(${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
      box.style.display = "flex";
    }
  }

  async executeDatasetUpload() {
    if (!this.selectedDatasetFile) return;

    const errBox = document.getElementById("datasetUploadError");
    if (errBox) errBox.style.display = "none";

    const reader = new FileReader();
    reader.onload = async (e) => {
      const csvText = e.target.result;
      try {
        const res = await this.fetchWithAuth("/api/admin/dataset/upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ csv_content: csvText })
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
          if (errBox) {
            const detail = data.detail || {};
            let errText = detail.error || "Dataset upload failed.";
            if (detail.missing_columns && detail.missing_columns.length > 0) {
              errText += ` Missing required columns: ${detail.missing_columns.join(", ")}`;
            }
            errBox.innerText = errText;
            errBox.style.display = "block";
          }
          return;
        }

        this.showToast(`Dataset updated! Ingested ${data.total_records} complaints.`);
        document.getElementById("selectedFileBox").style.display = "none";
        this.selectedDatasetFile = null;
        this.loadDatasetSummary();
        this.loadAdminComplaints();
        this.loadKPIs();
        this.loadQueue();
        this.renderCharts();
        this.addAuditEntry("Dataset Uploaded", this.currentUser.name, `Ingested replacement dataset with ${data.total_records} rows`);
      } catch (err) {
        console.error(err);
        if (errBox) {
          errBox.innerText = "Error uploading dataset to server.";
          errBox.style.display = "block";
        }
      }
    };
    reader.readAsText(this.selectedDatasetFile);
  }

  exportDataset() {
    window.open("/api/admin/dataset/export", "_blank");
    this.showToast("Dataset export started.");
  }

  async confirmResetDataset() {
    if (confirm("Reset active dataset back to pristine 5,500 historical complaints baseline?")) {
      try {
        const res = await this.fetchWithAuth("/api/admin/dataset/reset", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          this.showToast("Dataset successfully restored to default 5,500 records!");
          this.loadDatasetSummary();
          this.loadAdminComplaints();
          this.loadKPIs();
          this.loadQueue();
          this.renderCharts();
          this.addAuditEntry("Dataset Reset", this.currentUser?.name || "Admin", "Restored default 5,500 record baseline");
        }
      } catch (err) {
        console.error(err);
      }
    }
  }

  // --- Audit Logs ---
  loadAuditLogs() {
    if (this.auditLogs.length === 0) {
      this.auditLogs = [
        { time: "Just now", action: "User Sign In", user: this.currentUser?.name || "Dr. K. V. Raman", role: this.currentUser?.role || "admin", target: "Session Token", details: "Signed in with HMAC session credentials", status: "Success" },
        { time: "10 mins ago", action: "Pipeline Evaluation", user: "AI Engine", role: "system", target: "CMP-2026-0001", details: "Classified category as Water Cooler with 0.88 confidence", status: "Success" },
        { time: "25 mins ago", action: "Priority Recalculation", user: "Priority Engine", role: "system", target: "5,500 Records", details: "Recalculated queue using active prototype weights", status: "Success" },
        { time: "1 hour ago", action: "Dataset Validation", user: "System Loader", role: "system", target: "campus_complaints_dataset.csv", details: "Cleaned and verified 5,500 complaint rows across 21 columns", status: "Success" }
      ];
    }
    this.renderAuditLogsTable();
  }

  addAuditEntry(action, user, details) {
    const now = new Date().toLocaleTimeString();
    this.auditLogs.unshift({
      time: now,
      action: action,
      user: user,
      role: this.currentUser?.role || "admin",
      target: "Complaint Store",
      details: details,
      status: "Success"
    });
    this.renderAuditLogsTable();
  }

  renderAuditLogsTable() {
    const tbody = document.getElementById("auditLogsTableBody");
    if (!tbody) return;

    tbody.innerHTML = this.auditLogs.map(l => `
      <tr>
        <td style="font-family:monospace; font-size:0.78rem;">${l.time}</td>
        <td><strong>${l.action}</strong></td>
        <td>${l.user}</td>
        <td><span class="user-role-tag role-${l.role.toLowerCase()}">${l.role}</span></td>
        <td><code>${l.target}</code></td>
        <td style="font-size:0.82rem; color:var(--text-muted);">${l.details}</td>
        <td><span class="badge badge-open">${l.status}</span></td>
      </tr>
    `).join("");
  }

  refreshAuditLogs() {
    this.loadAuditLogs();
    this.showToast("Audit logs refreshed.");
  }

  // --- Form & Sandbox Setup (Existing Preserved) ---
  setupForms() {
    const form = document.getElementById("complaintForm");
    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        this.submitComplaint();
      });
    }

    const runSandbox = document.getElementById("runSandboxBtn");
    if (runSandbox) {
      runSandbox.addEventListener("click", () => this.runSandboxPipeline());
    }

    this.prefillScenario("water_cooler");
  }

  prefillScenario(type) {
    const scenarios = {
      "water_cooler": {
        name: "Arjun Sharma",
        role: "Student",
        facility: "Water Cooler",
        location: "Block C (Science & Labs)",
        desc: "The water cooler near Block C 2nd floor laboratory has stopped working again and water is leaking on the floor. Many students use it during lunch hours."
      },
      "washroom_leak": {
        name: "Priya Patel",
        role: "Student",
        facility: "Washroom & Plumbing",
        location: "Central Cafeteria & Food Court",
        desc: "Main washroom near cafeteria food court has severe tap leakage and water logging causing slippery surface near lunch queue."
      },
      "server_ac": {
        name: "Dr. Ramesh Nair",
        role: "Faculty",
        facility: "HVAC & Air Conditioning",
        location: "Block B (Computing & IT Wing)",
        desc: "Server room AC unit in Block B ground floor is making loud rattling noise and ambient temperature is rising above 28 degrees celsius."
      },
      "library_light": {
        name: "Siddharth Verma",
        role: "Student",
        facility: "Lighting & Electrical",
        location: "Central Library",
        desc: "Flickering fluorescent tube light in the 3rd floor quiet study zone creating buzzing noise and headache for students."
      }
    };

    const sc = scenarios[type];
    if (sc) {
      const rName = document.getElementById("reporterName");
      const rRole = document.getElementById("reporterRole");
      const fType = document.getElementById("facilityType");
      const lSelect = document.getElementById("locationSelect");
      const cDesc = document.getElementById("complaintDesc");

      if (rName) rName.value = sc.name;
      if (rRole) rRole.value = sc.role;
      if (fType) fType.value = sc.facility;
      if (lSelect) lSelect.value = sc.location;
      if (cDesc) cDesc.value = sc.desc;
    }
  }

  async submitComplaint() {
    const submitBtn = document.getElementById("submitBtn");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = "Analyzing with AI Pipeline...";
    }

    const payload = {
      reporter_name: document.getElementById("reporterName")?.value.trim() || "Student",
      reporter_role: document.getElementById("reporterRole")?.value || "Student",
      facility_type: document.getElementById("facilityType")?.value || "Water Cooler",
      location: document.getElementById("locationSelect")?.value || "Block C (Science & Labs)",
      description: document.getElementById("complaintDesc")?.value.trim() || ""
    };

    try {
      const res = await fetch("/api/complaints/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        this.renderSubmissionResult(data.record, data.pipeline_analysis);
        this.showToast("Complaint submitted & prioritized successfully!");
        this.loadKPIs();
        this.loadQueue();
      } else {
        this.showToast("Error processing complaint.", "error");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Network error submitting complaint.", "error");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit & Run AI Prioritization Pipeline";
      }
    }
  }

  renderSubmissionResult(record, analysis) {
    this.lastAnalyzedRecord = record;
    const ph = document.getElementById("resultPlaceholder");
    const rc = document.getElementById("resultContent");
    if (ph) ph.style.display = "none";
    if (rc) rc.style.display = "block";

    document.getElementById("resCategory").innerText = analysis.predicted_category;
    document.getElementById("resConfidence").innerText = `Confidence: ${(analysis.category_confidence * 100).toFixed(0)}%`;
    document.getElementById("resSeverity").innerText = analysis.predicted_severity;
    document.getElementById("resSevScore").innerText = `Calibrated Score: ${analysis.severity_score}/100`;

    document.getElementById("resRecurrence").innerText = analysis.recurrence_detected ? `Yes (${analysis.recurrence_count} Prior)` : "No (First Time)";
    document.getElementById("resRecurrenceBadge").innerText = analysis.recurrence_count >= 5 ? "Chronic Problem" : (analysis.recurrence_detected ? "Recurring" : "Isolated");
    document.getElementById("resLocationRisk").innerText = `${analysis.location_risk} Risk Zone`;
    document.getElementById("resFootfall").innerText = `Footfall: ${analysis.footfall_level} (${analysis.footfall_score}/100)`;

    document.getElementById("resPriorityScore").innerHTML = `${analysis.priority_score.toFixed(1)} <span style="font-size:1rem; font-weight:600; color:var(--text-muted);">/ 100</span>`;
    document.getElementById("resImpactBadge").innerText = `Impact: ${analysis.expected_impact}`;
    document.getElementById("resAction").innerText = analysis.recommended_action;

    const inspectBtn = document.getElementById("inspectShapBtn");
    if (inspectBtn) {
      inspectBtn.onclick = () => {
        this.openTicketDetail(record.id || record.complaint_id);
      };
    }
  }

  async runSandboxPipeline() {
    const input = document.getElementById("sandboxInput")?.value.trim();
    if (!input) {
      this.showToast("Please enter complaint text to test.", "error");
      return;
    }

    try {
      const res = await fetch("/api/analyze-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reporter_name: "Sandbox User",
          reporter_role: "Student",
          facility_type: "Water Cooler",
          location: "Central Cafeteria & Food Court",
          description: input
        })
      });
      const data = await res.json();
      if (data.success) {
        const an = data.analysis;
        document.getElementById("sbStage1Cat").innerText = `Category: ${an.predicted_category}`;
        document.getElementById("sbStage1Keys").innerText = `Keywords: ${an.extracted_keywords.slice(0, 4).join(", ")}`;
        document.getElementById("sbStage2Sev").innerText = `Severity: ${an.predicted_severity}`;
        document.getElementById("sbStage2Score").innerText = `Score: ${an.severity_score}/100`;
        document.getElementById("sbStage3Rec").innerText = `Recurrence: ${an.recurrence_detected ? "Yes" : "No"}`;
        document.getElementById("sbStage3Count").innerText = `Count: ${an.recurrence_count}`;
        document.getElementById("sbStage4Loc").innerText = `Risk: ${an.location_risk}`;
        document.getElementById("sbStage4Foot").innerText = `Footfall: ${an.footfall_level}`;
        document.getElementById("sbStage5Pri").innerText = `Score: ${an.priority_score} / 100`;
        document.getElementById("sbStage5Impact").innerText = `Impact: ${an.expected_impact}`;
        document.getElementById("sbPrescribedAction").innerText = an.recommended_action;
        this.showToast("Pipeline executed live!");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Pipeline error.", "error");
    }
  }

  // --- Dynamic Dashboard KPIs ---
  async loadKPIs() {
    try {
      const res = await fetch("/api/kpi");
      const kpis = await res.json();

      const kTot = document.getElementById("kpiTotal");
      const kOp = document.getElementById("kpiOpen");
      const kHP = document.getElementById("kpiHighPri");
      const kRec = document.getElementById("kpiRecurring");
      const kHR = document.getElementById("kpiHighRisk");
      const kAvg = document.getElementById("kpiAvgRes");

      if (kTot) kTot.innerText = (kpis.total_complaints || 5500).toLocaleString();
      if (kOp) kOp.innerText = (kpis.open_complaints || 0).toLocaleString();
      if (kHP) kHP.innerText = (kpis.high_priority_issues || 0).toLocaleString();
      if (kRec) kRec.innerText = (kpis.recurring_issues || 0).toLocaleString();
      if (kHR) kHR.innerText = kpis.high_risk_facilities || 0;
      if (kAvg) kAvg.innerHTML = `${kpis.avg_resolution_hours || 21.4} <span style="font-size:0.9rem; font-weight:500;">hrs</span>`;
    } catch (err) {
      console.error("Failed loading KPIs", err);
    }
  }

  setupFilters() {
    const filters = ["filterSource", "filterStatus", "filterSeverity", "filterFacility"];
    filters.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener("change", () => this.loadComplaintsWithFilters());
      }
    });
  }

  async loadComplaintsWithFilters() {
    const src = document.getElementById("filterSource")?.value;
    const status = document.getElementById("filterStatus")?.value;
    const sev = document.getElementById("filterSeverity")?.value;
    const fac = document.getElementById("filterFacility")?.value;

    const params = new URLSearchParams();
    if (src) params.append("data_source", src);
    if (status && status !== "All") params.append("status", status);
    if (sev && sev !== "All") params.append("severity", sev);
    if (fac && fac !== "All") params.append("facility_type", fac);

    try {
      const res = await fetch(`/api/complaints?${params.toString()}`);
      const data = await res.json();
      this.cachedComplaints = data;
      const b = document.getElementById("activeFilterBadge");
      if (b) b.innerText = `Showing ${data.length} records`;
      this.renderCharts();
    } catch (err) {
      console.error(err);
    }
  }

  // --- Analytics Charts (Chart.js) ---
  async renderCharts() {
    if (this.cachedComplaints.length === 0) {
      const res = await fetch("/api/complaints?limit=500");
      this.cachedComplaints = await res.json();
    }
    const complaints = this.cachedComplaints;

    const isDark = this.theme === "dark";
    const textColor = isDark ? "#cbd5e1" : "#475569";
    const gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";

    // Chart 1: Issue Distribution
    const categoryCounts = {};
    complaints.forEach(c => {
      const cat = c.predicted_category || c.facility_type || c.facility_category || "General Facilities";
      categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
    });

    const catCtx = document.getElementById("categoryChart");
    if (catCtx) {
      if (this.charts.cat) this.charts.cat.destroy();
      this.charts.cat = new Chart(catCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(categoryCounts),
          datasets: [{
            data: Object.values(categoryCounts),
            backgroundColor: [
              "#3b82f6", "#06b6d4", "#f97316", "#10b981", "#8b5cf6", "#ec4899", "#eab308"
            ],
            borderWidth: isDark ? 2 : 1,
            borderColor: isDark ? "#1e293b" : "#ffffff"
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "right", labels: { color: textColor, font: { size: 11 } } }
          }
        }
      });
    }

    // Chart 2: Severity Distribution
    const sevCounts = { "Critical": 0, "High": 0, "Medium": 0, "Low": 0 };
    complaints.forEach(c => {
      const s = c.predicted_severity || c.severity || "Medium";
      if (sevCounts[s] !== undefined) sevCounts[s]++;
    });

    const sevCtx = document.getElementById("severityChart");
    if (sevCtx) {
      if (this.charts.sev) this.charts.sev.destroy();
      this.charts.sev = new Chart(sevCtx, {
        type: "bar",
        data: {
          labels: Object.keys(sevCounts),
          datasets: [{
            label: "Complaints Count",
            data: Object.values(sevCounts),
            backgroundColor: ["#ef4444", "#f97316", "#eab308", "#10b981"],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: textColor }, grid: { display: false } },
            y: { ticks: { color: textColor }, grid: { color: gridColor } }
          }
        }
      });
    }

    // Chart 3: Trends Over Time
    const trendDates = ["Aug 15", "Aug 22", "Aug 29", "Sep 05", "Sep 12", "Sep 18"];
    const inflowData = [450, 680, 890, 1340, 1890, 2450];
    const resolvedData = [390, 580, 780, 1150, 1620, 2180];

    const trCtx = document.getElementById("trendsChart");
    if (trCtx) {
      if (this.charts.tr) this.charts.tr.destroy();
      this.charts.tr = new Chart(trCtx, {
        type: "line",
        data: {
          labels: trendDates,
          datasets: [
            {
              label: "Cumulative Inflow",
              data: inflowData,
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.1)",
              fill: true,
              tension: 0.35
            },
            {
              label: "Resolved Tickets",
              data: resolvedData,
              borderColor: "#10b981",
              backgroundColor: "transparent",
              borderDash: [5, 5],
              tension: 0.35
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: textColor } }
          },
          scales: {
            x: { ticks: { color: textColor }, grid: { display: false } },
            y: { ticks: { color: textColor }, grid: { color: gridColor } }
          }
        }
      });
    }

    // Chart 4: Location Concentration
    const locCounts = {};
    complaints.forEach(c => {
      const loc = (c.location || c.building_name || "").split("(")[0].trim();
      if (loc) locCounts[loc] = (locCounts[loc] || 0) + 1;
    });

    const locCtx = document.getElementById("locationChart");
    if (locCtx) {
      if (this.charts.loc) this.charts.loc.destroy();
      this.charts.loc = new Chart(locCtx, {
        type: "bar",
        data: {
          labels: Object.keys(locCounts).slice(0, 8),
          datasets: [{
            label: "Complaints Concentration",
            data: Object.values(locCounts).slice(0, 8),
            backgroundColor: "#8b5cf6",
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: textColor }, grid: { color: gridColor } },
            y: { ticks: { color: textColor }, grid: { display: false } }
          }
        }
      });
    }
  }

  // --- Priority Queue ---
  async loadQueue() {
    try {
      const res = await fetch("/api/priority-queue?limit=50");
      const queue = await res.json();
      const tbody = document.getElementById("priorityQueueBody");
      if (!tbody) return;
      tbody.innerHTML = "";

      queue.forEach((item) => {
        const tr = document.createElement("tr");

        const score = Number(item.priority_score || 50).toFixed(1);
        let scoreColor = "var(--risk-low)";
        if (score >= 75) scoreColor = "var(--risk-critical)";
        else if (score >= 50) scoreColor = "var(--risk-medium)";

        const sourceBadge = item.is_demo 
          ? `<span class="badge badge-demo">Dataset</span>` 
          : `<span class="badge badge-live">Live</span>`;

        const ticketId = item.complaint_id || item.id || item.ticket_number;
        const sev = item.predicted_severity || item.severity || "Medium";

        tr.innerHTML = `
          <td><strong>${ticketId}</strong></td>
          <td>${sourceBadge}</td>
          <td>
            <strong>${item.facility_type || item.facility_category}</strong>
            <div style="font-size:0.75rem; color:var(--text-muted);">${item.location || item.building_name}</div>
          </td>
          <td>
            <span class="badge badge-${sev.toLowerCase()}">${sev}</span>
          </td>
          <td>
            ${item.recurrence_detected ? `<span class="badge badge-critical">Yes (${item.recurrence_count || item.recurring_count_30d || 1})</span>` : `<span class="badge badge-low">No</span>`}
          </td>
          <td>${item.footfall_level || "Medium"}</td>
          <td>
            <div class="priority-meter-box">
              <span class="priority-score-number" style="color:${scoreColor};">${score}</span>
              <div class="priority-progress-bar">
                <div class="priority-fill" style="width:${score}%; background-color:${scoreColor};"></div>
              </div>
            </div>
          </td>
          <td style="font-size:0.82rem; max-width:240px;">
            ${item.recommended_action || "Standard work order dispatch"}
          </td>
          <td>
            <select class="filter-select" style="padding:4px 8px; font-size:0.78rem;" onchange="app.updateTicketStatus('${ticketId}', this.value)">
              <option value="Open" ${item.status === "Open" ? "selected" : ""}>Open</option>
              <option value="In Progress" ${item.status === "In Progress" ? "selected" : ""}>In Progress</option>
              <option value="Resolved" ${item.status === "Resolved" ? "selected" : ""}>Resolved</option>
            </select>
          </td>
          <td>
            <button class="btn btn-outline" style="padding:4px 8px; font-size:0.75rem;" onclick="app.openTicketDetail('${ticketId}')">
              Why?
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
    }
  }

  async updateTicketStatus(id, newStatus) {
    try {
      const res = await fetch(`/api/complaints/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(`Ticket ${id} status updated to ${newStatus}`);
        this.loadKPIs();
        this.loadQueue();
        if (this.currentView === "admin-complaints") this.loadAdminComplaints();
        this.addAuditEntry("Status Updated", this.currentUser?.name || "Admin", `Changed status of ${id} to ${newStatus}`);
      }
    } catch (err) {
      console.error(err);
      this.showToast("Failed to update status", "error");
    }
  }

  // --- Facility Risk Matrix ---
  async loadRiskMatrix() {
    try {
      const res = await fetch("/api/risk-intelligence");
      const matrix = await res.json();
      const tbody = document.getElementById("riskMatrixBody");
      if (!tbody) return;
      tbody.innerHTML = "";

      matrix.forEach(item => {
        const tr = document.createElement("tr");
        let badgeCls = "low";
        if (item.risk_tier === "High") badgeCls = "critical";
        else if (item.risk_tier === "Medium") badgeCls = "medium";

        tr.innerHTML = `
          <td><strong>${item.location_name}</strong></td>
          <td>${item.zone}</td>
          <td>${item.footfall_tier} (${item.footfall_score}/100)</td>
          <td><strong>${item.risk_score} / 100</strong></td>
          <td><span class="badge badge-${badgeCls}">${item.risk_tier}</span></td>
          <td>${item.active_complaints} Open</td>
          <td>${item.recurring_complaints} Recurring</td>
          <td style="font-size:0.8rem; color:var(--text-muted);">
            ${item.risk_tier === "High" ? "Conduct preventive sweep of drinking & sanitation units" : "Standard weekly scheduled maintenance"}
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
    }
  }

  // --- Chronic Recurrence Profile ---
  async loadRecurringData() {
    try {
      const res = await fetch("/api/recurring-issues");
      const data = await res.json();
      const highlight = data.chronic_highlight;
      const list = document.getElementById("chronicTimelineList");
      if (!list) return;
      list.innerHTML = "";

      highlight.failure_timeline.forEach((item, idx) => {
        const row = document.createElement("div");
        row.style.cssText = "display:flex; justify-content:space-between; align-items:center; background:var(--bg-card); border:1px solid var(--border-main); padding:10px 14px; border-radius:6px; font-size:0.82rem;";
        row.innerHTML = `
          <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-weight:700; color:var(--primary);">#${idx + 1}</span>
            <span style="color:var(--text-muted); font-family:monospace;">${item.date}</span>
            <strong>${item.complaint}</strong>
          </div>
          <div style="display:flex; align-items:center; gap:12px;">
            <span style="color:var(--text-muted);">Action: <em>${item.action}</em></span>
            ${item.days_to_next ? `<span class="badge badge-medium">${item.days_to_next}d to next fail</span>` : `<span class="badge badge-critical">Active Ticket</span>`}
          </div>
        `;
        list.appendChild(row);
      });
    } catch (err) {
      console.error(err);
    }
  }

  // --- Predictive Issue-Risk Forecasting ---
  async loadForecasts() {
    try {
      const res = await fetch("/api/predictive-maintenance");
      const data = await res.json();
      const container = document.getElementById("forecastsContainer");
      if (!container) return;
      container.innerHTML = "";

      data.forecasts.forEach(f => {
        const card = document.createElement("div");
        card.className = "card";
        card.style.borderTop = `4px solid ${f.forecasted_risk_level === "High" ? "var(--risk-critical)" : "var(--risk-medium)"}`;

        const factorList = f.prediction_factors.map(factor => `<li>${factor}</li>`).join("");

        card.innerHTML = `
          <div class="card-header">
            <div>
              <span class="badge badge-${f.forecasted_risk_level === "High" ? "critical" : "medium"}">
                ${f.forecasted_risk_level} Risk Window (~${f.predicted_window_days} Days)
              </span>
              <h4 style="font-size:1.05rem; font-weight:700; margin-top:6px;">${f.facility}</h4>
              <p style="font-size:0.8rem; color:var(--text-muted);">${f.location}</p>
            </div>
            <div style="text-align:right;">
              <div style="font-size:0.72rem; color:var(--text-muted);">Confidence</div>
              <div style="font-size:1.2rem; font-weight:800; color:var(--primary);">${(f.confidence_score * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div style="margin-bottom:14px;">
            <div style="font-size:0.75rem; text-transform:uppercase; font-weight:700; color:var(--text-muted); margin-bottom:4px;">Risk Assessment Drivers:</div>
            <ul style="font-size:0.8rem; color:var(--text-muted); margin-left:18px; line-height:1.5;">
              ${factorList}
            </ul>
          </div>

          <div style="background:var(--bg-card-subtle); padding:10px 12px; border-radius:6px; margin-bottom:14px;">
            <div style="font-size:0.72rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Recommended Preventive Action:</div>
            <div style="font-size:0.82rem; font-weight:600; color:var(--text-main); margin-top:2px;">${f.recommended_preventive_action}</div>
          </div>

          <button class="btn btn-outline" style="width:100%; font-size:0.78rem;" onclick="app.showToast('Preventive work order created for ${f.facility}')">
            Schedule Preventive Inspection
          </button>
        `;
        container.appendChild(card);
      });
    } catch (err) {
      console.error(err);
    }
  }

  // --- Interactive Campus SVG Map ---
  async loadCampusMap() {
    try {
      const res = await fetch("/api/campus-locations");
      const locations = await res.json();
      const svg = document.getElementById("campusSvgMap");
      if (!svg) return;

      let svgHtml = `
        <rect width="1000" height="600" fill="var(--bg-card-subtle)" rx="10"/>
        <path d="M 100 280 L 900 280 M 500 80 L 500 520 M 250 150 L 750 480" stroke="var(--border-main)" stroke-width="12" fill="none"/>
      `;

      locations.forEach(loc => {
        const cx = loc.x * 10;
        const cy = loc.y * 6;
        const isHigh = loc.footfall_score >= 85;
        const color = isHigh ? "var(--risk-critical)" : (loc.footfall_score >= 65 ? "var(--primary)" : "var(--risk-low)");

        svgHtml += `
          <g style="cursor:pointer;" onclick="app.selectCampusLocation('${loc.name}', '${loc.zone}', ${loc.footfall_score}, '${loc.footfall}')">
            ${isHigh ? `<circle cx="${cx}" cy="${cy}" r="38" fill="${color}" opacity="0.2"><animate attributeName="r" values="30;46;30" dur="2s" repeatCount="indefinite"/></circle>` : ""}
            <rect x="${cx - 45}" y="${cy - 30}" width="90" height="60" rx="8" fill="var(--bg-card)" stroke="${color}" stroke-width="2.5"/>
            <text x="${cx}" y="${cy - 6}" font-size="11" font-weight="700" fill="var(--text-main)" text-anchor="middle">${loc.name.split(" ")[0]} ${loc.name.split(" ")[1] || ""}</text>
            <text x="${cx}" y="${cy + 14}" font-size="9" font-weight="600" fill="${color}" text-anchor="middle">Footfall: ${loc.footfall_score}</text>
          </g>
        `;
      });

      svg.innerHTML = svgHtml;
    } catch (err) {
      console.error(err);
    }
  }

  selectCampusLocation(name, zone, footfallScore, footfallTier) {
    const box = document.getElementById("selectedBuildingBox");
    if (!box) return;
    box.style.display = "block";
    document.getElementById("selLocName").innerText = name;
    document.getElementById("selLocRisk").innerText = footfallScore >= 80 ? "Elevated Footfall Zone" : "Standard Zone";
    document.getElementById("selLocRisk").className = `badge badge-${footfallScore >= 80 ? "critical" : "medium"}`;
    document.getElementById("selLocDetails").innerText = `Zone: ${zone} • Pedestrian Footfall Rating: ${footfallTier} (${footfallScore}/100)`;

    const matching = this.cachedComplaints.filter(c => ((c.location || c.building_name) || "").toLowerCase().includes(name.toLowerCase().split(" ")[0]));
    document.getElementById("selLocStats").innerHTML = `
      <span class="badge badge-demo">${matching.length} Active Tickets on File</span>
      <span class="badge badge-inprogress">${matching.filter(m => m.recurrence_detected).length} Chronic Recurrences</span>
      <button class="btn btn-outline" style="padding:2px 8px; font-size:0.72rem;" onclick="app.navigateTo('priority-queue')">Inspect In Queue →</button>
    `;
  }

  // --- Explainable AI (SHAP) ---
  async loadTicketDetail(ticketId) {
    try {
      const res = await fetch(`/api/complaints/${ticketId}`);
      return await res.json();
    } catch (err) {
      console.error(err);
      return null;
    }
  }

  async openTicketDetail(ticketId) {
    const rec = await this.loadTicketDetail(ticketId);
    if (!rec) {
      this.showToast("Ticket record not found", "error");
      return;
    }

    const modal = document.getElementById("ticketDetailModal");
    modal.classList.add("active");

    document.getElementById("mdlTicketNumber").innerText = rec.complaint_id || rec.id || rec.ticket_number;
    document.getElementById("mdlTicketTitle").innerText = `${rec.facility_type || rec.facility_category} (${rec.location || rec.building_name})`;

    const expl = rec.shap_explanation;
    let waterfallHtml = "";

    if (expl && expl.features) {
      expl.features.forEach(f => {
        const isPos = f.shap_value >= 0;
        const widthPct = Math.min(100, Math.max(10, Math.abs(f.shap_value) * 4));
        waterfallHtml += `
          <div class="shap-row">
            <div class="shap-meta">
              <div class="shap-meta-name">${f.feature_name}</div>
              <div class="shap-meta-desc">${f.description}</div>
            </div>
            <div class="shap-bar-container">
              <div class="shap-bar ${isPos ? "positive" : "negative"}" style="width:${widthPct}%;">
                ${isPos ? "+" : ""}${f.shap_value.toFixed(1)} pts
              </div>
            </div>
            <div class="shap-val-text" style="color:${isPos ? "var(--shap-positive)" : "var(--shap-negative)"};">
              ${isPos ? "+" : ""}${f.shap_value.toFixed(1)}
            </div>
          </div>
        `;
      });
    }

    document.getElementById("ticketDetailBody").innerHTML = `
      <div style="background:var(--bg-card-subtle); padding:14px; border-radius:8px; margin-bottom:18px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <span style="font-size:0.75rem; color:var(--text-muted);">Reporter: <strong>${rec.reporter_name} (${rec.reporter_role || "Student"})</strong></span>
          <span style="font-size:0.75rem; color:var(--text-muted);">Status: <strong>${rec.status}</strong></span>
        </div>
        <p style="font-size:0.88rem; font-style:italic;">"${rec.complaint_text || rec.description}"</p>
      </div>

      <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-bottom:18px;">
        <div style="background:var(--bg-card-subtle); padding:10px; border-radius:6px;">
          <div style="font-size:0.72rem; color:var(--text-muted);">Calculated Priority</div>
          <div style="font-size:1.4rem; font-weight:800; color:var(--primary);">${Number(rec.priority_score || 50).toFixed(1)} / 100</div>
        </div>
        <div style="background:var(--bg-card-subtle); padding:10px; border-radius:6px;">
          <div style="font-size:0.72rem; color:var(--text-muted);">Predicted Severity</div>
          <div style="font-size:1.1rem; font-weight:700;">${rec.predicted_severity || rec.severity}</div>
        </div>
        <div style="background:var(--bg-card-subtle); padding:10px; border-radius:6px;">
          <div style="font-size:0.72rem; color:var(--text-muted);">Recurrence Count</div>
          <div style="font-size:1.1rem; font-weight:700;">${rec.recurrence_count || rec.recurring_count_30d || 0} Previous</div>
        </div>
      </div>

      <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:10px;">SHAP Feature Attribution Waterfall:</h4>
      <div class="shap-waterfall-box" style="margin-bottom:14px;">
        ${waterfallHtml}
      </div>

      <div style="background:var(--primary-light); padding:12px; border-radius:6px; font-size:0.82rem; color:var(--text-main);">
        ${expl ? expl.summary : "Shapley game-theoretic decomposition generated by mathematical explainer."}
      </div>
    `;
  }

  closeTicketDetail() {
    const modal = document.getElementById("ticketDetailModal");
    if (modal) modal.classList.remove("active");
  }

  // --- ML Model Metrics ---
  async loadModelMetrics() {
    try {
      const res = await fetch("/api/model-metrics");
      const data = await res.json();

      const nlp = data.nlp_classifier;
      if (nlp) {
        document.getElementById("nlpModelName").innerText = nlp.model_name;
        document.getElementById("nlpAcc").innerText = `${(nlp.accuracy * 100).toFixed(1)}%`;
        document.getElementById("nlpF1").innerText = `${(nlp.weighted_f1_score * 100).toFixed(1)}%`;
        document.getElementById("nlpNote").innerText = nlp.benchmark_note;
      }

      const sev = data.severity_model;
      if (sev) {
        document.getElementById("sevModelName").innerText = sev.model_name;
        document.getElementById("sevAcc").innerText = `${(sev.accuracy * 100).toFixed(1)}%`;
        document.getElementById("sevF1").innerText = `${(sev.weighted_f1_score * 100).toFixed(1)}%`;
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- Configurable Prototype Weights ---
  setupModals() {
    const wBtn = document.getElementById("weightsModalBtn");
    if (wBtn) {
      wBtn.addEventListener("click", () => {
        document.getElementById("weightsModal").classList.add("active");
      });
    }

    const tBtn = document.getElementById("launchTourBtn");
    if (tBtn) {
      tBtn.addEventListener("click", () => {
        this.startTour();
      });
    }
  }

  closeWeightsModal() {
    document.getElementById("weightsModal").classList.remove("active");
  }

  async loadWeights() {
    try {
      const res = await fetch("/api/settings/weights");
      const weights = await res.json();
      this.activeWeights = weights;

      document.getElementById("sliderSev").value = Math.round(weights.weight_severity * 100);
      document.getElementById("sliderRec").value = Math.round(weights.weight_recurrence * 100);
      document.getElementById("sliderFoot").value = Math.round(weights.weight_footfall * 100);
      document.getElementById("sliderLoc").value = Math.round(weights.weight_location_risk * 100);
      document.getElementById("sliderImp").value = Math.round(weights.weight_impact * 100);

      this.updateSliderLabels();
    } catch (err) {
      console.error(err);
    }
  }

  updateSliderLabels() {
    const sSev = parseInt(document.getElementById("sliderSev").value);
    const sRec = parseInt(document.getElementById("sliderRec").value);
    const sFoot = parseInt(document.getElementById("sliderFoot").value);
    const sLoc = parseInt(document.getElementById("sliderLoc").value);
    const sImp = parseInt(document.getElementById("sliderImp").value);

    document.getElementById("lblWeightSev").innerText = `${sSev}%`;
    document.getElementById("lblWeightRec").innerText = `${sRec}%`;
    document.getElementById("lblWeightFoot").innerText = `${sFoot}%`;
    document.getElementById("lblWeightLoc").innerText = `${sLoc}%`;
    document.getElementById("lblWeightImp").innerText = `${sImp}%`;
  }

  async saveWeights() {
    const sSev = parseFloat(document.getElementById("sliderSev").value) / 100.0;
    const sRec = parseFloat(document.getElementById("sliderRec").value) / 100.0;
    const sFoot = parseFloat(document.getElementById("sliderFoot").value) / 100.0;
    const sLoc = parseFloat(document.getElementById("sliderLoc").value) / 100.0;
    const sImp = parseFloat(document.getElementById("sliderImp").value) / 100.0;

    const payload = {
      weight_severity: sSev,
      weight_recurrence: sRec,
      weight_footfall: sFoot,
      weight_location_risk: sLoc,
      weight_impact: sImp
    };

    try {
      const res = await fetch("/api/settings/weights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        this.activeWeights = data.active_weights;
        this.showToast("Weights updated! Priority queue recalculated.");
        this.closeWeightsModal();
        this.loadQueue();
        if (this.currentView === "admin-complaints") this.loadAdminComplaints();
      }
    } catch (err) {
      console.error(err);
      this.showToast("Failed to update weights", "error");
    }
  }

  resetDefaultWeights() {
    document.getElementById("sliderSev").value = 35;
    document.getElementById("sliderRec").value = 25;
    document.getElementById("sliderFoot").value = 20;
    document.getElementById("sliderLoc").value = 10;
    document.getElementById("sliderImp").value = 10;
    this.updateSliderLabels();
  }

  // --- 5-Minute Guided Tour ---
  startTour() {
    this.tourStep = 0;
    this.renderTourStep();
    document.getElementById("tourModal").classList.add("active");
  }

  renderTourStep() {
    const step = this.tourSteps[this.tourStep];
    document.getElementById("tourStepBadge").innerText = step.badge;
    document.getElementById("tourTitle").innerText = step.title;
    document.getElementById("tourBody").innerHTML = step.content;

    document.getElementById("tourPrevBtn").style.display = this.tourStep === 0 ? "none" : "block";
    document.getElementById("tourNextBtn").innerText = this.tourStep === this.tourSteps.length - 1 ? "Finish Tour" : "Next Step →";

    // Auto-navigate user to corresponding page
    this.navigateTo(step.view);
  }

  nextTourStep() {
    if (this.tourStep < this.tourSteps.length - 1) {
      this.tourStep++;
      this.renderTourStep();
    } else {
      this.closeTour();
      this.showToast("5-Minute Walkthrough Complete!");
    }
  }

  prevTourStep() {
    if (this.tourStep > 0) {
      this.tourStep--;
      this.renderTourStep();
    }
  }

  jumpTourView() {
    const step = this.tourSteps[this.tourStep];
    this.navigateTo(step.view);
    this.closeTour();
  }

  closeTour() {
    document.getElementById("tourModal").classList.remove("active");
  }

  // --- Toast System ---
  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    if (type === "error") {
      toast.style.borderLeftColor = "var(--risk-critical)";
    }
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }
}

// Instantiate App
const app = new SmartCampusApp();
window.app = app;
