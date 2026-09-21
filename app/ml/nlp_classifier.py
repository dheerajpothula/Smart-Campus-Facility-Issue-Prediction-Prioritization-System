"""
NLP Text Processing and Facility Category Classification Model.
Trains a Scikit-Learn TF-IDF + Classifier pipeline on campus facility complaint text.
Generates genuine evaluation metrics (accuracy, precision, recall, f1, confusion matrix).
"""

import re
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from app.ml.eval_utils import stratified_train_test_split, compute_classification_metrics

# Rich training corpus representing diverse campus maintenance complaint utterances
TRAINING_SAMPLES = [
    # Water Cooler
    ("The water cooler near Block C 2nd floor laboratory has stopped working again and water is leaking on the floor.", "Water Cooler"),
    ("Water dispenser outside library is dispensing warm water instead of cold.", "Water Cooler"),
    ("Water fountain near gym is completely dry and making humming sound.", "Water Cooler"),
    ("Water cooler tap is loose and spraying water when pressed.", "Water Cooler"),
    ("Filtration unit on 3rd floor water cooler is clogged and flow is a slow trickle.", "Water Cooler"),
    ("Water cooler tray is overflowing and causing puddle in the main corridor.", "Water Cooler"),
    ("Water from cooler tastes metallic and smells unpleasant.", "Water Cooler"),
    ("Push button on drinking water unit in Block B is jammed.", "Water Cooler"),
    ("Water cooler compressor overheating and smelling like burnt rubber.", "Water Cooler"),
    ("Water purifier filter replacement light is flashing red in Block A.", "Water Cooler"),

    # Washroom & Plumbing
    ("Main washroom near cafeteria food court has severe tap leakage and water logging.", "Washroom & Plumbing"),
    ("Toilet flush in 1st floor boys washroom is broken and water running continuously.", "Washroom & Plumbing"),
    ("Severe sewage odor coming from drainage pipe in Block D washrooms.", "Washroom & Plumbing"),
    ("Washbasin pipe ruptured under counter causing flooding in female restroom.", "Washroom & Plumbing"),
    ("No water supply in hostel wing B washrooms since early morning.", "Washroom & Plumbing"),
    ("Urinal auto-sensor not flushing and drain trap clogged with hair.", "Washroom & Plumbing"),
    ("Restroom door latch broken and flush handle snapped off.", "Washroom & Plumbing"),
    ("Soap dispenser broken and wet floor slippery near washroom entrance.", "Washroom & Plumbing"),
    ("Clogged floor drain causing standing water in shower area.", "Washroom & Plumbing"),
    ("Plumbing leakage from ceiling dripping onto restroom mirror.", "Washroom & Plumbing"),

    # Lighting & Electrical
    ("Flickering fluorescent tube light in the 3rd floor study room buzzing loudly.", "Lighting & Electrical"),
    ("Sparks observed from electrical wall socket on bench 4 in chemistry lab.", "Lighting & Electrical"),
    ("Complete power outage in Block B computer lab, MCB tripped.", "Lighting & Electrical"),
    ("Hallway ceiling lights are dead making the staircase pitch dark at night.", "Lighting & Electrical"),
    ("Loose electrical wire hanging from false ceiling near classroom 104.", "Lighting & Electrical"),
    ("Switchboard sparking when plugging in laptop charger in library.", "Lighting & Electrical"),
    ("High bay floodlights in basketball court are flickering and dim.", "Lighting & Electrical"),
    ("Emergency exit sign illumination light battery failed.", "Lighting & Electrical"),
    ("Short circuit smell near main distribution board in Block C basement.", "Lighting & Electrical"),
    ("Classroom fan regulator broken and fan running at dangerous vibrating speed.", "Lighting & Electrical"),

    # HVAC & Air Conditioning
    ("Server room AC unit in Block B is making loud rattling noise and temperature rising.", "HVAC & Air Conditioning"),
    ("Air conditioner in seminar hall is blowing hot air and not cooling room.", "HVAC & Air Conditioning"),
    ("Central AC duct leaking water drops directly onto student study desks.", "HVAC & Air Conditioning"),
    ("Ventilation fan in chemistry lab is not exhausting fumes properly.", "HVAC & Air Conditioning"),
    ("HVAC thermostat stuck at 30 degrees and room is uncomfortably hot and humid.", "HVAC & Air Conditioning"),
    ("Auditorium air cooling system making deafening squealing noise from belt.", "HVAC & Air Conditioning"),
    ("Exhaust fan in cafeteria kitchen has stopped rotating, kitchen filled with smoke.", "HVAC & Air Conditioning"),
    ("Air conditioning unit remote receiver not responding and cooling off.", "HVAC & Air Conditioning"),
    ("Cold airflow completely blocked due to frozen evaporator coils in library.", "HVAC & Air Conditioning"),
    ("HVAC chiller pump failure causing entire building temperature to surge.", "HVAC & Air Conditioning"),

    # Waste Management & Sanitation
    ("External organic compost waste bin overflowing behind cafeteria loading dock.", "Waste Management & Sanitation"),
    ("Trash cans outside seminar hall overflowing with paper cups and food boxes.", "Waste Management & Sanitation"),
    ("Stray dogs ripped open garbage bags outside student dining hall.", "Waste Management & Sanitation"),
    ("Sanitary waste disposal bin not cleared for past three days in hostel.", "Waste Management & Sanitation"),
    ("Litter and plastic bottles scattered all across sports arena bleachers.", "Waste Management & Sanitation"),
    ("Rotting food waste in open bins attracting swarms of flies near courtyard.", "Waste Management & Sanitation"),
    ("Chemical waste storage carboy in biology lab needs safe disposal.", "Waste Management & Sanitation"),
    ("Recycling bins knocked over and paper waste flying across campus walkway.", "Waste Management & Sanitation"),
    ("Severe accumulation of wet waste in central quad creating health hazard.", "Waste Management & Sanitation"),
    ("Sanitation crew missed morning clearing in Block E academic corridor.", "Waste Management & Sanitation"),

    # Elevator & Mobility
    ("Passenger elevator #2 in Block A is halting abruptly and doors not opening.", "Elevator & Mobility"),
    ("Lift stuck between 2nd and 3rd floor with warning alarm ringing.", "Elevator & Mobility"),
    ("Elevator floor leveling uneven by 3 inches creating major tripping hazard.", "Elevator & Mobility"),
    ("Lift buttons for 4th and 5th floors unresponsive in Block C.", "Elevator & Mobility"),
    ("Wheelchair ramp handrail loose and wobbling dangerously near entrance.", "Elevator & Mobility"),
    ("Elevator motor grinding sound when descending with passengers.", "Elevator & Mobility"),
    ("Emergency intercom inside elevator car #1 has no dial tone or response.", "Elevator & Mobility"),
    ("Elevator door safety light sensor failed, closing on boarding students.", "Elevator & Mobility"),
    ("Service elevator out of order since yesterday causing supply delay.", "Elevator & Mobility"),
    ("Lift ventilation fan dead and emergency display screen corrupted.", "Elevator & Mobility"),

    # Classroom AV & Furniture
    ("Ceiling projector in Lecture Hall 204 has faded bulb and power cable loose.", "Classroom AV & Furniture"),
    ("HDMI projector input flickering blue screen during ongoing faculty lecture.", "Classroom AV & Furniture"),
    ("Lab chairs in room 102 have broken hydraulic cylinders and torn edges.", "Classroom AV & Furniture"),
    ("Classroom desk bench collapsed when student sat down, screws detached.", "Classroom AV & Furniture"),
    ("Podium wireless microphone crackling with static feedback.", "Classroom AV & Furniture"),
    ("Whiteboard mounting bracket loose and tilting forward on the wall.", "Classroom AV & Furniture"),
    ("Sound amplifier in auditorium audio console dead, no audio output.", "Classroom AV & Furniture"),
    ("Window blind mechanism cord snapped leaving sunlight glaring on projection.", "Classroom AV & Furniture"),
    ("Conference room motorized projector screen jammed halfway down.", "Classroom AV & Furniture"),
    ("Computer lab ergonomic workstation table leg bent and unstable.", "Classroom AV & Furniture")
]

class NLPClassifier:
    """Manages text vectorization, category classification, and model performance metrics."""

    def __init__(self):
        self.pipeline: Pipeline = None
        self.classes_: list = []
        self.metrics: Dict[str, Any] = {}
        self._train_and_evaluate()

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _train_and_evaluate(self):
        texts = [self._clean_text(item[0]) for item in TRAINING_SAMPLES]
        labels = [item[1] for item in TRAINING_SAMPLES]

        # Stratified train/test split
        X_train, X_test, y_train, y_test = stratified_train_test_split(
            texts, labels, test_size=0.20, random_state=42
        )

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=500,
                sublinear_tf=True
            )),
            ("clf", MultinomialNB(alpha=0.1))
        ])

        self.pipeline.fit(X_train, y_train)
        self.classes_ = list(self.pipeline.classes_)

        # Evaluate on holdout test partition
        y_pred = list(self.pipeline.predict(X_test))
        eval_res = compute_classification_metrics(y_test, y_pred, self.classes_)

        self.metrics = {
            "model_name": "TF-IDF (1-2 ngrams) + Complement/Multinomial Naive Bayes",
            "train_samples_count": len(X_train),
            "test_samples_count": len(X_test),
            "accuracy": eval_res.get("accuracy", 0.0),
            "weighted_precision": eval_res.get("weighted_precision", 0.0),
            "weighted_recall": eval_res.get("weighted_recall", 0.0),
            "weighted_f1_score": eval_res.get("weighted_f1_score", 0.0),
            "classes": self.classes_,
            "confusion_matrix": eval_res.get("confusion_matrix", []),
            "per_class_metrics": eval_res.get("per_class_metrics", {}),
            "is_demo_evaluation": True,
            "benchmark_note": "Evaluated on genuine 80/20 stratified holdout partition with Scikit-learn."
        }

    def predict(self, raw_text: str) -> Tuple[str, float, Dict[str, float]]:
        cleaned = self._clean_text(raw_text)
        probs = self.pipeline.predict_proba([cleaned])[0]
        top_idx = int(np.argmax(probs))
        predicted_class = self.classes_[top_idx]
        confidence = float(probs[top_idx])

        all_probs = {cls_name: round(float(probs[i]), 3) for i, cls_name in enumerate(self.classes_)}
        return predicted_class, confidence, all_probs

    def extract_keywords(self, raw_text: str) -> list:
        cleaned = self._clean_text(raw_text)
        words = cleaned.split()
        stop_words = {"the", "a", "an", "is", "in", "near", "and", "to", "for", "of", "on", "it", "at", "with", "from"}
        meaningful = [w for w in words if w not in stop_words and len(w) > 2]
        return list(dict.fromkeys(meaningful))[:8]

# Singleton instance
nlp_model = NLPClassifier()
