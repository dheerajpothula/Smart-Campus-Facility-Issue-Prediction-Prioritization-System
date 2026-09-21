# Smart Campus Facility Issue Prediction & Prioritization System

> **An AI/ML-powered campus maintenance platform that analyzes historical student and staff complaints, predicts facility failure risks, detects recurring problems, computes explainable priority scores (0–100), forecasts future high-risk windows, and provides maintenance teams with an intelligent dispatch queue.**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Scikit--Learn](https://img.shields.io/badge/Scikit--Learn-1.5+-F7931E.svg)](https://scikit-learn.org/)
[![SHAP](https://img.shields.io/badge/Explainability-SHAP-red.svg)](https://github.com/slundberg/shap)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Project Concept & Value Proposition

Traditional college campus maintenance portals operate merely as **passive complaint bins**:
1. Complaints are stored chronologically without urgency intelligence.
2. Trivial cosmetic defects bury critical infrastructure hazards (e.g. electrical sparks or server room overheating).
3. Chronic failures (such as the Block C water cooler failing 12 times) receive repeated temporary patch repairs rather than root-cause overhauls.
4. Maintenance supervisors lack visibility into pedestrian footfall density and failure recurrence.

**The Smart Campus AI System changes this paradigm:**
$$\mathbf{Complaint \longrightarrow AI\ Analysis \longrightarrow Risk\ \&\ Severity\ Prediction \longrightarrow Priority\ (0\text{--}100) \longrightarrow Targeted\ Action}$$

---

## 2. 5-Minute Understanding Flow

The platform includes a built-in **interactive 5-Minute Guided Walkthrough Tour** that enables any evaluator or visitor to grasp the entire workflow without prior technical knowledge:

| Time | Stage | Focus |
| :--- | :--- | :--- |
| **0:00 – 1:00** | **Problem & Purpose** | Why passive complaint inboxes fail and how predictive AI triage prevents major campus disruptions. |
| **1:00 – 2:00** | **Complaint Intake** | Plain English complaint submission; instant automated extraction of facility type, severity, and recurrence. |
| **2:00 – 3:00** | **7-Stage ML Pipeline** | Interactive pipeline debugger demonstrating NLP, severity estimation, footfall mapping, and priority scoring. |
| **3:00 – 4:00** | **Maintenance Dashboard** | KPI monitoring, issue distribution charts, and the intelligent dispatch queue with live status toggling. |
| **4:00 – 5:00** | **Predictive AI & SHAP** | Forward-looking 7–30 day issue-risk forecasts and game-theoretic SHAP waterfall feature attribution. |

---

## 3. End-to-End System Architecture

```
                       [ Student / Staff Complaint ]
                                    │
                                    ▼
                     [ FastAPI Asynchronous Backend ]
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    │                                                               │
    ▼                                                               ▼
[ NLP Classifier (TF-IDF + NB) ]               [ Severity Estimator (TF-IDF + ML) ]
Classifies Facility Domain                     Estimates Physical Urgency & Hazard
(Water Cooler, Plumbing, Lighting, etc.)       (Low, Medium, High, Critical)
    │                                                               │
    └───────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                    [ Historical Recurrence Engine ]
                    Scans Campus DB for matching pairs
                    Identifies Chronic Outages & MTBF
                                    │
                                    ▼
                    [ Campus Location Risk Engine ]
                    Maps Zone Footfall & Vulnerability
                    (e.g., Block C = 88/100 Lunch Footfall)
                                    │
                                    ▼
             [ Intelligent Priority Scoring Engine (0 - 100) ]
             Configurable Prototype Weights (Severity, Recurrence,
             Footfall, Location Risk, Operational Impact)
                                    │
                                    ▼
                 [ Exact Shapley / SHAP Explainer ]
                 Decomposes Score into Positive & Negative Drivers
                 Efficiency: Base Value + Σ(φ_i) = Final Priority
                                    │
                                    ▼
          [ Maintenance Priority Dispatch Queue & Dashboard ]
          Real-time triage, status management (Open/In Progress/Resolved)
```

---

## 4. Configurable Prototype Priority Formula

Priority is calculated dynamically using a transparent, explainable formula:

$$\text{Priority Score} = w_{\text{sev}} \cdot S + w_{\text{rec}} \cdot R + w_{\text{foot}} \cdot F + w_{\text{loc\_risk}} \cdot L + w_{\text{imp}} \cdot I$$

Where:
* $S$: Calibrated Severity Score ($0 \le S \le 100$)
* $R$: Historical Recurrence Score ($0 \le R \le 100$)
* $F$: Location Pedestrian Footfall ($0 \le F \le 100$)
* $L$: Chronic Location Vulnerability Index ($0 \le L \le 100$)
* $I$: Operational Impact Score ($0 \le I \le 100$)

### Default Prototype Weights:
* **Severity Weight ($w_{\text{sev}}$):** `0.35` (35%)
* **Recurrence Weight ($w_{\text{rec}}$):** `0.25` (25%)
* **Footfall Weight ($w_{\text{foot}}$):** `0.20` (20%)
* **Location Risk Weight ($w_{\text{loc}}$):** `0.10` (10%)
* **Impact Weight ($w_{\text{imp}}$):** `0.10` (10%)

> **Interactive Feature**: Weights can be adjusted live via sliders in the **Weights Modal** in the UI, instantly re-ranking the entire maintenance dispatch queue.

---

## 5. Explainable AI: Mathematical SHAP Formulation

To eliminate "black-box" skepticism, every ticket features an exact **SHAP (SHapley Additive exPlanations)** decomposition based on cooperative game theory:

$$\text{Priority}(x) = \phi_0 + \sum_{i=1}^M \phi_i(x)$$

* **$\phi_0$ (Base Value):** The expected campus baseline priority score ($\approx 54.5$ pts).
* **$\phi_i$ (Shapley Attribution):** $\phi_i = w_i \cdot (x_i - E[X_i])$.
  * **Positive $\phi_i$ (Red/Rose):** Pushes priority **UP** (e.g. high footfall zone, repeated failure history).
  * **Negative $\phi_i$ (Blue/Teal):** Pulls priority **DOWN** (e.g. low-traffic building, first-time occurrence).

---

## 6. Data Integrity & Transparent Separation

* **Historical Demo Dataset (`is_demo = True`):** Pre-seeded with 20 realistic campus incident patterns across Blocks A–E, Library, Cafeteria, Hostels, and Sports Arena (including the Block C 12-complaint chronic case study).
* **Live Campus Tickets (`is_demo = False`):** All user submissions made through the web form are saved and tagged as real-time tickets (`LIVE-XXXXXX` / `CMP-2026-85X`).
* **Predictive Issue-Risk Forecasting:** Explicitly labeled as:
  > *“Prediction ≠ Confirmed Physical Breakdown. Algorithmic issue-risk forecast indicating elevated complaint probability based on historical recurrence cycles and footfall telemetry.”*

---

## 7. Quick Start & Execution

### Prerequisites
* Python 3.10+ (Tested on Python 3.12)
* Any modern web browser (Chrome, Edge, Firefox, Safari)

### Installation & Execution

```bash
# 1. Clone or navigate to the project directory
cd Unsuper

# 2. Launch the application (starts FastAPI & web server)
.\.venv\Scripts\python.exe run_server.py
```

Open your browser at:
👉 **`http://127.0.0.1:8000`**

### Running Automated Test Suite
```bash
.\.venv\Scripts\python.exe tests/test_system.py
```

---

## 8. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/kpi` | Aggregated campus KPIs (total, open, high priority, avg resolution) |
| `GET` | `/api/complaints` | Filtered complaints (`data_source`, `status`, `severity`, `facility`) |
| `GET` | `/api/complaints/{id}` | Single ticket details with full SHAP explanation breakdown |
| `POST` | `/api/complaints/submit` | Real-time intake running full 7-stage ML pipeline |
| `POST` | `/api/analyze-preview` | Sandbox endpoint for testing text without saving to database |
| `PATCH` | `/api/complaints/{id}/status` | Updates status (`Open` → `In Progress` → `Resolved`) |
| `GET` | `/api/priority-queue` | Sorted dispatch queue by calculated priority score |
| `GET` | `/api/risk-intelligence` | Campus location risk matrix & vulnerability rankings |
| `GET` | `/api/recurring-issues` | Chronic recurrence profiles & failure timeline |
| `GET` | `/api/predictive-maintenance` | 7–30 day forward-looking issue-risk forecasts |
| `GET` | `/api/model-metrics` | Genuine Scikit-learn holdout evaluation metrics |
| `GET` | `/api/settings/weights` | Current active prototype priority weights |
| `POST` | `/api/settings/weights` | Updates weights and recalculates open ticket priorities |
| `POST` | `/api/reset-demo-data` | Restores database to initial pristine demo dataset |

---

## 9. Viva & College Presentation Q&A Guide

**Q1: How does this system differ from an ordinary complaint ticketing portal?**  
> *A: Standard portals only store tickets chronologically. This system executes an ML pipeline that classifies the problem, estimates hazard severity, identifies chronic recurrence, checks campus footfall exposure, computes an explainable 0–100 priority score, and forecasts future failure windows.*

**Q2: How is the priority score calculated?**  
> *A: We use a multi-factor weighted combination: Severity (35%), Recurrence (25%), Footfall (20%), Location Risk (10%), and Expected Operational Impact (10%). All weights are configurable prototype parameters.*

**Q3: How do you explain the AI predictions to non-technical maintenance supervisors?**  
> *A: We use game-theoretic SHAP (Shapley Additive exPlanations) values to break down the exact positive and negative point contributions relative to the campus baseline, accompanied by plain-language diagnostic recommendations.*

**Q4: How does the system detect recurring issues?**  
> *A: It cross-references incoming facility types and locations against historical resolution logs and scans for linguistic recurrence markers (e.g. "again", "third time", "repeatedly"), computing the Mean Time Between Failures (MTBF).*
