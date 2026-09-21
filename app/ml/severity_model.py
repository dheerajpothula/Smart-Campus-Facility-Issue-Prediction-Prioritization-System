"""
Predictive Severity Model.
Analyzes linguistic urgency signals, hazard indicators, facility criticality,
and footfall exposure to classify issue severity (Low, Medium, High, Critical)
and assign a continuous severity score (0 - 100).
"""

import re
from typing import Tuple, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from app.ml.eval_utils import stratified_train_test_split, compute_classification_metrics

SEVERITY_TRAINING_DATA = [
    # Critical
    ("Sparks observed from electrical wall socket in chemistry laboratory.", "Critical"),
    ("Lift stuck between floors with passenger alarm ringing continuously.", "Critical"),
    ("Server room AC unit failure ambient temperature rising above thermal limit.", "Critical"),
    ("Exposed live electrical wiring dangling in main lecture hall corridor.", "Critical"),
    ("Severe water pipe burst flooding computer lab basement with equipment.", "Critical"),
    ("Elevator jerky descent and emergency braking mechanism failing.", "Critical"),
    ("Chemical odor and fume exhaust failure inside biology research facility.", "Critical"),
    ("Short circuit smoke emerging from power distribution panel.", "Critical"),

    # High
    ("Water cooler near Block C 2nd floor laboratory stopped working and water leaking on floor during lunch.", "High"),
    ("Main washroom near cafeteria food court has severe tap leakage causing slippery floor.", "High"),
    ("External organic compost waste bin overflowing behind food court loading bay.", "High"),
    ("Restroom flush continuously running and water logging hallway entrance.", "High"),
    ("Air conditioning unit completely dead in central library during peak exams.", "High"),
    ("Passenger elevator halting abruptly and doors struggling to open.", "High"),
    ("Drinking water machine filter tap broken and water spraying on pathway.", "High"),
    ("Foul sewage odor permeating entire hostel wing ground floor.", "High"),

    # Medium
    ("Flickering fluorescent tube light in 3rd floor quiet study zone buzzing loudly.", "Medium"),
    ("Low water pressure in 2nd floor showers on North Hostel Wing B during morning.", "Medium"),
    ("Water cooler on ground floor dispensing warm water instead of chilled.", "Medium"),
    ("Lab chairs in room 102 have broken hydraulic lifts and torn fabric.", "Medium"),
    ("Ceiling projector in lecture hall has faded dim lamp bulb.", "Medium"),
    ("Drain in men's washroom backing up with mild standing water.", "Medium"),
    ("Recycling bins outside mess hall knocked over with plastic bottles.", "Medium"),
    ("Window blind mechanism jammed leaving morning sun glare on board.", "Medium"),

    # Low
    ("Floodlights in basketball court have one bulb dead leaving minor shadow.", "Low"),
    ("Emergency exit sign illumination beeping softly on low backup battery.", "Low"),
    ("Minor paint peeling and small wall plaster crack near stairwell.", "Low"),
    ("Locker room trash bin full after basketball practice empty bottles.", "Low"),
    ("Door hinge squeaking when opened in faculty lounge.", "Low"),
    ("Whiteboard marker ledge loose on seminar room wall.", "Low"),
    ("Restroom mirror has small smudge mark along bottom corner.", "Low"),
    ("Clock on classroom wall is running ten minutes slow.", "Low")
]

class SeverityModel:
    """Predicts discrete severity level and continuous calibrated severity score."""

    SEVERITY_SCORES = {
        "Low": 35.0,
        "Medium": 58.0,
        "High": 82.0,
        "Critical": 95.0
    }

    HAZARD_KEYWORDS = {
        "spark", "sparks", "smoke", "fire", "shock", "electric", "short circuit",
        "stuck", "trapped", "flood", "flooding", "burst", "hazard", "dangerous",
        "emergency", "injury", "burn", "slippery", "explosion"
    }

    URGENCY_KEYWORDS = {
        "immediately", "urgent", "critical", "again", "stopped", "overflowing",
        "broken", "failed", "exam", "lunch", "peak", "leak", "leaking", "foul"
    }

    def __init__(self):
        self.pipeline: Pipeline = None
        self.classes_ = ["Low", "Medium", "High", "Critical"]
        self.metrics: Dict[str, Any] = {}
        self._train_and_evaluate()

    def _train_and_evaluate(self):
        texts = [item[0].lower() for item in SEVERITY_TRAINING_DATA]
        labels = [item[1] for item in SEVERITY_TRAINING_DATA]

        X_train, X_test, y_train, y_test = stratified_train_test_split(
            texts, labels, test_size=0.25, random_state=42
        )

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=350, sublinear_tf=True)),
            ("clf", MultinomialNB(alpha=0.2))
        ])

        self.pipeline.fit(X_train, y_train)

        y_pred = list(self.pipeline.predict(X_test))
        eval_res = compute_classification_metrics(y_test, y_pred, self.classes_)

        self.metrics = {
            "model_name": "TF-IDF + Multinomial Naive Bayes Severity Estimator",
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": eval_res.get("accuracy", 0.0),
            "weighted_precision": eval_res.get("weighted_precision", 0.0),
            "weighted_recall": eval_res.get("weighted_recall", 0.0),
            "weighted_f1_score": eval_res.get("weighted_f1_score", 0.0),
            "per_class_metrics": eval_res.get("per_class_metrics", {}),
            "confusion_matrix": eval_res.get("confusion_matrix", []),
            "is_demo_evaluation": True
        }

    def predict(self, raw_text: str, footfall_score: float = 65.0) -> Tuple[str, float, float, Dict[str, Any]]:
        text_lower = raw_text.lower()
        probs = self.pipeline.predict_proba([text_lower])[0]
        class_prob_map = {cls: float(probs[idx]) for idx, cls in enumerate(self.pipeline.classes_)}

        # Keyword heuristics for safety critical anomalies
        has_hazard = any(k in text_lower for k in self.HAZARD_KEYWORDS)
        urgency_count = sum(1 for k in self.URGENCY_KEYWORDS if k in text_lower)

        top_class = str(self.pipeline.predict([text_lower])[0])
        confidence = class_prob_map.get(top_class, 0.85)

        # Safety override for overt electrical / entrapment hazards
        if has_hazard and top_class not in ["Critical", "High"]:
            top_class = "High"
            confidence = max(confidence, 0.88)

        base_score = self.SEVERITY_SCORES.get(top_class, 60.0)

        # Dynamic nuance adjustments
        nuance = (urgency_count * 2.5) + (footfall_score * 0.08)
        if has_hazard:
            nuance += 6.0

        calculated_score = float(np.clip(base_score + nuance - 5.0, 15.0, 100.0))

        signals = {
            "has_hazard_keywords": has_hazard,
            "urgency_keywords_detected": urgency_count,
            "class_probabilities": {k: round(v, 3) for k, v in class_prob_map.items()}
        }

        return top_class, round(confidence, 2), round(calculated_score, 1), signals

severity_model = SeverityModel()
