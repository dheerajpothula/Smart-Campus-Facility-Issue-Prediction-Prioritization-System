"""
Model Insights Page.
Presents machine learning model evaluation, feature importances, and diagnostic metrics.
"""
import streamlit as st
from dashboard.components.styles import render_section_header
from dashboard.components.empty_state import render_empty_state


def render_page() -> None:
    """Renders the Model Insights view."""
    render_section_header(
        title="Machine Learning Model Insights & Architecture",
        subtitle="Pipeline specifications, TF-IDF vectorization parameters, and academic validation protocols.",
        badge="Architecture Specs",
    )

    # Empty State Display with light-theme styling
    render_empty_state(
        title="Model Registry & Evaluation Logs",
        subtitle="Current models are using domain-informed heuristics and TF-IDF baselines.",
        description=(
            "Training pipelines in `src/training/` produce model artifacts (*.joblib / *.pkl) as datasets grow. "
            "Inspect the live 'Explainable AI (SHAP)' and 'AI Analysis Pipeline' tabs in the navigation to see active inference in action."
        ),
        action_notes=[
            "TF-IDF vectorizer fits on campus complaint descriptions (unigrams + bigrams).",
            "Supervised multi-class categorization (Electrical, Plumbing, HVAC, IT, Civil).",
            "Recurrence risk scoring evaluated with Stratified 5-Fold Cross Validation.",
            "Explainable AI (SHAP) feature importance exposed in the dedicated SHAP tab.",
        ],
        icon="🧪",
        badge_label="Status: Baseline Heuristics Active",
    )

    st.markdown("---")

    # ML Pipeline Specifications
    st.subheader("🔬 Machine Learning Pipeline Design")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            #### 1. Text Feature Extraction (TF-IDF)
            - **Algorithm**: Term Frequency-Inverse Document Frequency
            - **Configuration**:
                - `ngram_range`: (1, 2) to capture compound domain phrases (e.g., "water leakage", "short circuit", "fan capacitor").
                - `sublinear_tf`: True (dampens the impact of recurring words).
                - `min_df`: 2 (filters rare single-occurrence typos).
                - `max_features`: 1,000–2,500 domain-specific terms.
                - `stop_words`: English stopwords augmented with campus-specific stopwords.
            """
        )

        st.markdown(
            """
            #### 2. Categorization Classifier
            - **Target**: Issue Department / Subsystem (Electrical, Plumbing, HVAC, IT Infrastructure, Civil/Carpentry).
            - **Candidate Models**:
                - *Multinomial Naive Bayes*: Fast, robust baseline for sparse text features.
                - *Logistic Regression (L2)*: Highly interpretable feature coefficients.
                - *Random Forest / Gradient Boosting*: Robust against non-linear interactions.
            """
        )

    with col2:
        st.markdown(
            r"""
            #### 3. Recurrence & Failure Predictor
            - **Target**: Binary classification ($y \in \{0, 1\}$) indicating whether this facility component will fail again within 30 days.
            - **Input Features**:
                - Location encoding (Block, Floor, Zone type).
                - Historical complaint frequency in trailing 60 days.
                - Mean time between past complaints.
                - TF-IDF severity terms.
            - **Evaluation Protocol**: Stratified K-Fold Cross-Validation (K=5) to avoid class-imbalance leakage.
            """
        )

    st.markdown("---")

    # Planned Evaluation Protocol & Reporting Standard
    st.subheader("📊 Rigorous Academic Evaluation Protocol")
    st.markdown(
        """
        To maintain strict academic integrity as a CSE AIML project:
        - **No Synthetic Metrics**: All metrics shown are computed from verified validation splits (`src/evaluation/`).
        - **Imbalance Handling**: Performance will be judged primarily on **Macro F1-Score** and **Balanced Accuracy**, rather than misleading raw accuracy.
        - **Confusion Matrix**: Multi-class breakdown across departments will be visualised to detect cross-domain confusion (e.g., electrical water heater categorized under plumbing vs electrical).
        """
    )
