# Smart Campus Facility Issue Prediction & Prioritization System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework Streamlit](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Theme Light](https://img.shields.io/badge/theme-Light%20Professional-2563eb.svg)]()
[![Status Prototype](https://img.shields.io/badge/status-Role--Based%20v0.3.0-success.svg)]()

An intelligent university maintenance intelligence platform engineered to identify, prioritize, and predict recurring facility breakdowns across university campuses with role-based user access, student complaint tracking, and sequential token assignment.

---

## 🎨 UI/UX Architecture & Student Complaint Tracking

The platform features a modern, clean **Light Theme** with distinct access tiers for Students and Administrators.

### 1. Minimal Role Selection Gateway
Before accessing the main website, a clean role selection gateway displays two profiles:
1. **Administrator**:
   "Full facility intelligence access with maintenance analytics, AI predictions, priority management, and recurring issue tracking."
2. **Student**:
   "Report campus facility issues and track your requests, progress, and estimated repair dates."

### 2. Student Dashboard & Complaint Isolation
- **Student Data Isolation**: The student portal displays strictly the complaints submitted by the currently logged-in student under **"My Complaints"**. Pre-existing sample tickets and complaints belonging to other students are never displayed.
- **Empty State**: If the student has submitted 0 complaints, a clean empty state is displayed:
  - Title: *"No complaints submitted yet."*
  - Subtitle: *"Raise an issue to report a facility problem on campus."*
  - Features a prominent **"Raise an Issue"** action button.
- **Raise an Issue Form**: A clean, focused submission form with exactly 7 fields (without asterisk symbols):
  1. `Student ID` (auto-filled from active session)
  2. `Student Name` (auto-filled or editable)
  3. `Issue Title / Brief Headline`
  4. `Facility Category` (6 standard categories: Washroom cleanliness, Garbage overflow, Water cooler or water supply, Electrical or lighting issues, Plumbing, Other maintenance issues)
  5. `Building or Block`
  6. `Floor or Specific Location`
  7. `Detailed Issue Description`
- **Actions**: "Submit Issue" and "Cancel" buttons with subtle submission loading spinner and input validation.
- **Sequential Token Assignment**: Every complaint receives a permanent token in the format:
  `CMP-2026-001`, `CMP-2026-002`, `CMP-2026-003`... (3-digit zero-padded, sequential, unique).
- **Confirmation Message**:
  *"Issue submitted successfully. Your complaint token is CMP-2026-XXX. Track your complaint progress from My Complaints."*
- **5-Stage Repair Progress Indicator**: Replaces internal priority labels and scores on student cards:
  `Submitted` ➔ `Under Review` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`
  - Active stage is prominently highlighted.
  - No priority badges (Low, Medium, High, Critical) or internal ML risk percentages are visible to students.

### 3. Administrator Dashboard & Management Integration
- Administrators view all campus requests, including student-submitted issues with `Student ID` and `Student Name`.
- Inspect automated ML predictions: Severity, Location Criticality, Recurrence Risk, Multi-Criteria Priority Score (0–100), and SLA dates.
- Status management controls allow administrators to update any complaint's progress across the 5 canonical stages.
- Changes made by administrators immediately propagate to the student's progress tracking timeline.

---

## 📂 Project Structure

```text
smart-campus-facility-prediction/
├── app.py                           # Application orchestrator with Role-Based Access Control
├── requirements.txt                 # Core dependencies (Streamlit, Pandas, NumPy, Scikit-learn)
├── README.md                        # Project documentation & execution guide
├── .gitignore                       # Git ignore rules for venv, caches, and models
├── .streamlit/
│   └── config.toml                  # Enforced light theme configuration
│
├── data/                            # Data storage
│   ├── raw/                         # Raw university complaint logs (CSV/Excel)
│   ├── processed/                   # complaints.json (persisted records with CMP-2026-XXX tokens)
│   └── synthetic/                   # Generated synthetic campus dataset
│
├── models/                          # Serialized model artifacts & TF-IDF vectorizers
│
├── src/                             # Core Python package
│   ├── data/
│   │   ├── __init__.py
│   │   └── complaints_store.py      # Token generator, persistence, and student filtering
│   ├── prediction/
│   │   ├── __init__.py
│   │   └── priority_scoring.py      # Multi-Criteria Priority Index (MCPI) & weight configuration
│   ├── preprocessing/               # Text cleaning & stopword filtering
│   ├── features/                    # TF-IDF vectorization & spatial-temporal features
│   ├── training/                    # Model training routines
│   └── evaluation/                  # Academic evaluation metrics
│
├── dashboard/                       # Streamlit UI layer
│   ├── components/
│   │   ├── role_selection.py        # Clean role selection screen (Admin vs Student)
│   │   ├── sidebar.py               # Admin navigation menu & demo controls
│   │   ├── empty_state.py           # Uniform labeled empty-state widget
│   │   └── styles.py                # Light theme CSS & 5-stage progress indicator
│   └── pages/
│       ├── overview.py              # Maintenance Operations Dashboard (KPIs & distributions)
│       ├── complaint_management.py  # Unified register & Admin status updates
│       ├── ai_analysis.py           # 5-stage automated AI decision pipeline
│       ├── maintenance_priorities.py# Intelligent Priority Queue & dispatch table
│       ├── predictive_analytics.py  # Predictive maintenance & risk forecasting
│       ├── recurring_issues.py      # Chronic recurring failure surveillance
│       ├── explainable_ai.py        # SHAP feature attribution & interpretability
│       ├── settings_weights.py      # Configurable priority weights ($w_1, w_2, w_3, w_4$)
│       ├── student_dashboard.py     # Student portal with "My Complaints" & "Raise an Issue"
│       └── model_insights.py        # ML architecture & academic validation standards
│
└── tests/                           # Automated test suite
    ├── test_initialization.py       # Baseline structure & symbol tests
    ├── test_redesign.py             # Redesign, badges, weights, and KPI tests
    ├── test_role_routing.py         # Role isolation and routing verification tests
    ├── test_student_raise_issue.py  # Student submission & status propagation tests
    └── test_final_refinement.py     # Complete acceptance criteria verification tests
```

---

## 🚀 How to Run the Application

In your terminal or PowerShell prompt:

```powershell
cd smart-campus-facility-prediction
streamlit run app.py
```

The application will launch in your browser at:
`http://localhost:8501`

---

## 🧪 Running Automated Tests

Run the complete 30-test suite via Python unittest:

```powershell
python -m unittest discover -s smart-campus-facility-prediction/tests
```
