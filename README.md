# Smart Campus Facility Issue Prediction & Prioritization System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework Streamlit](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Framework FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Theme Light](https://img.shields.io/badge/theme-Warm%20Chalk%20Light-EAE3D2.svg)]()
[![Tests Passing](https://img.shields.io/badge/tests-36%20passed-success.svg)]()
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An intelligent university maintenance intelligence platform engineered to identify, prioritize, and predict recurring facility breakdowns across university campuses with role-based access control, dedicated login, student complaint tracking, sequential token assignment, explainable AI (SHAP-inspired), and accessible high-contrast UI design.

---

## 🌟 Key Capabilities & Modules

### 1. Minimal Role Selection Gateway
- Clean, professional entry screen presenting two access tiers:
  - **Administrator**: *"Manage campus maintenance, facility issues, AI predictions, and maintenance priorities."*
  - **Student**: *"Report facility issues and track your complaints."*
- Choosing either role opens the dedicated login screen for that role.

### 2. Dedicated Role-Based Login Flow
- **Administrator Login**: Prompts for Administrator Name and Administrator ID.
- **Student Login**: Prompts for Student Name and Student ID.
- **Simulated Authentication**: Demonstrates realistic access control without requiring external passwords or emails.
- **Validation & Back Navigation**: Enforces non-empty name and ID inputs; provides a secondary "Back to Role Selection" button.
- **Dynamic Identity**: Binds the active session to the entered Name and ID (removing any hardcoded mock profiles).

### 3. Student Dashboard & Strict Data Isolation
- **Per-Student Complaint Isolation**: Students view strictly the complaints they have submitted under **My Complaints**.
- **Empty State**: If 0 complaints have been submitted by the student, shows:
  - *"No complaints submitted yet."*
  - *"Raise an issue to report a facility problem on campus."*
  - Prominent primary action button: `➕ Raise an Issue`.
- **Sequential Token Generation**: Assigns permanent, unique, 3-digit zero-padded tokens formatted as `CMP-2026-001`, `CMP-2026-002`, `CMP-2026-003`, etc.
- **7-Field Issue Submission Form**:
  1. *Student Name* (read-only, populated from authenticated session)
  2. *Student ID* (read-only, populated from authenticated session)
  3. *Issue Title / Brief Headline*
  4. *Facility Category* (Washroom cleanliness, Garbage overflow, Water supply, Electrical/lighting, Plumbing, Other)
  5. *Building or Block*
  6. *Floor or Specific Location*
  7. *Detailed Issue Description*
- **Confirmation Screen**: Displays ticket token, initial `Submitted` status, and a `Return to My Complaints` primary button without exposing raw JSON/code.
- **5-Stage Progress Indicator**: Visual progress tracker on each ticket (`Submitted` ➔ `Under Review` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`). Internal ML scores and priority weights are hidden from students.

### 4. Administrator Dashboard with Right-Side Sidebar
- **Layout**: Main dashboard analytics and controls on the **left**, and dedicated navigation sidebar on the **right**.
- **Right Sidebar Contents**:
  - Administrator identity (Name and ID entered during login).
  - Navigation menu with 8 core sections:
    1. **📊 Overview** (KPI metrics, facility distribution, location vulnerability density)
    2. **📋 Complaint Management** (Live tickets, student reporter badges, status updates across 5 stages, admin intake form, CSV ingestion)
    3. **⚡ AI Analysis** (NLP feature classification, tokenization, TF-IDF vectorization)
    4. **🚨 Priority Queue** (Dynamic multi-factor priority dispatch queue: Critical, High, Medium, Low)
    5. **🔮 Predictive Maintenance** (Failure recurrence forecasting and risk trajectories)
    6. **🔁 Recurring Issues** (Chronic repeat-breakdown detection and MTBF analysis)
    7. **🔬 Explainable AI** (SHAP-inspired multi-factor feature attribution and plain-language rationalization)
    8. **⚙️ Settings** (Interactive priority weight tuning and auto-normalization)
  - **Live Repository Status** (Total Tickets, Open Backlog, High Priority).
  - **Demo Controls** (Reset Default, Empty Dataset).
  - **Logout Button**: Clears the session and returns to the role selection gateway.

### 5. Accessible 60/30/10 Color Harmony & High-Contrast Buttons
- **60% Warm Chalk (`#FDFBF7`)**: Background canvas and spacious card sections.
- **30% Deep Charcoal (`#1A1A1A`)**: Typography, headings, icons, charts, and progress bars.
- **10% Soft Tan (`#EAE3D2`)**: Card borders, badges, status pills, and accents.
- **Primary Action Buttons**: Warm dark tan/brown background (`#756044`) with crisp white text (`#FFFFFF`) and dark hover (`#5D4A32`).
- **Secondary Action Buttons**: Soft Tan background (`#EAE3D2`) with Deep Charcoal text (`#1A1A1A`) and muted hover (`#D8CDB8`).
- **Outline & Disabled Buttons**: Transparent outline with visible text; disabled states remain clearly legible.

---

## 📂 Repository Structure

```
.
├── app.py                             # Root Streamlit Launcher
├── requirements.txt                   # Consolidated project dependencies
├── README.md                          # Main project documentation
├── LICENSE                            # MIT License
├── push_to_github.bat                 # Helper script for automated git push
├── run_server.py                      # FastAPI server launcher
├── start_server.bat                   # Batch script for FastAPI server
│
├── smart-campus-facility-prediction/  # Core Streamlit Intelligence Platform
│   ├── app.py                         # Streamlit application entry point
│   ├── requirements.txt               # Streamlit-specific requirements
│   ├── README.md                      # Detailed Streamlit architecture docs
│   ├── .gitignore                     # Repository exclusions
│   ├── dashboard/
│   │   ├── components/
│   │   │   ├── login_page.py          # Dedicated Administrator & Student login
│   │   │   ├── role_selection.py      # Gateway portal
│   │   │   ├── sidebar.py             # Right-side admin sidebar component
│   │   │   ├── styles.py              # Global 60/30/10 CSS & button contrast rules
│   │   │   └── empty_state.py         # Standardized empty state widget
│   │   └── pages/
│   │       ├── overview.py            # Overview metrics & charts
│   │       ├── complaint_management.py# Lifecycle dispatch & status updates
│   │       ├── student_dashboard.py   # Student portal & 7-field form
│   │       ├── ai_analysis.py         # NLP classification pipeline
│   │       ├── maintenance_priorities.py # Priority queue & crew dispatch
│   │       ├── predictive_analytics.py # Predictive risk analysis
│   │       ├── recurring_issues.py    # Recurrence detection & chronic analysis
│   │       ├── explainable_ai.py      # SHAP attribution breakdown
│   │       └── settings_weights.py    # Priority weight adjustment
│   ├── data/
│   │   ├── processed/complaints.json  # Persistent JSON ticket store
│   │   ├── raw/                       # Raw input data directory
│   │   └── synthetic/                 # Synthetic complaint generators
│   ├── src/
│   │   ├── data/complaints_store.py   # Ticket CRUD, sequential tokens, isolation
│   │   ├── prediction/priority_scoring.py # Multi-criteria scoring engine
│   │   ├── preprocessing/             # Text cleaning & tokenization
│   │   ├── features/                  # TF-IDF feature extractors
│   │   ├── training/                  # ML training scripts
│   │   └── evaluation/                # Model evaluation metrics
│   └── tests/                         # Comprehensive unit test suite (36 tests)
│       ├── test_final_refinement.py   # RBAC, login, sidebar & button tests
│       ├── test_student_raise_issue.py# Student issue intake & token tests
│       ├── test_redesign.py           # Priority weights & KPI tests
│       ├── test_role_routing.py       # Application router tests
│       └── test_initialization.py     # Structure & package import tests
│
└── app/                               # FastAPI Backend & Web Application
    ├── main.py                        # FastAPI REST API application
    ├── auth.py                        # JWT/Session authentication logic
    ├── data/                          # 5,500 historical complaint dataset & DB
    ├── ml/                            # ML pipeline, severity & risk engines
    ├── models/                        # Pydantic data schemas
    └── static/                        # Vanilla JS, HTML, CSS web assets
```

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install dependencies in your virtual environment:

```powershell
# Clone the repository
git clone https://github.com/dheerajpothula/Smart-Campus-Facility-Issue-Prediction-Prioritization-System.git
cd Smart-Campus-Facility-Issue-Prediction-Prioritization-System

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Launch Streamlit Intelligence Platform (Recommended)
Launch the primary interactive platform directly from workspace root:

```powershell
streamlit run app.py
```
*Or navigate to the subfolder:*
```powershell
cd smart-campus-facility-prediction
streamlit run app.py
```

### 3. Launch FastAPI REST Service & Web Interface (Alternative)
```powershell
python run_server.py
```
Open browser at: `http://127.0.0.1:8000`

---

## 🧪 Running Automated Tests

Run the comprehensive unit test suite:

```powershell
python -m unittest discover -s smart-campus-facility-prediction/tests
```

**Results:**
- **36 Unit Tests passing (100% pass rate)** covering role selection, dedicated login flow, student isolation, sequential `CMP-2026-XXX` tokens, 5-stage progress indicator, right sidebar navigation, button contrast tokens, and priority scoring algorithms.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
