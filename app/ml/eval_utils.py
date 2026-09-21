"""
Pure Python and NumPy Evaluation & Validation Utilities.
Guarantees 100% compatibility across enterprise environments, avoiding external C-extension
DLL blocks (e.g. Windows Application Control / WDAC policy blocks on mutual_info binaries).
"""

import random
from typing import List, Tuple, Dict, Any

def stratified_train_test_split(
    texts: List[str],
    labels: List[str],
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Splits texts and labels with stratified representation for each class."""
    rng = random.Random(random_state)
    
    # Group indices by class label
    class_indices: Dict[str, List[int]] = {}
    for idx, label in enumerate(labels):
        class_indices.setdefault(label, []).append(idx)
        
    train_indices = []
    test_indices = []
    
    for label, indices in class_indices.items():
        rng.shuffle(indices)
        n_test = max(1, int(round(len(indices) * test_size)))
        test_indices.extend(indices[:n_test])
        train_indices.extend(indices[n_test:])
        
    rng.shuffle(train_indices)
    rng.shuffle(test_indices)
    
    X_train = [texts[i] for i in train_indices]
    y_train = [labels[i] for i in train_indices]
    X_test = [texts[i] for i in test_indices]
    y_test = [labels[i] for i in test_indices]
    
    return X_train, X_test, y_train, y_test

def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    classes: List[str]
) -> Dict[str, Any]:
    """Computes exact Accuracy, Weighted Precision, Recall, F1, and Confusion Matrix."""
    total = len(y_true)
    if total == 0:
        return {}
        
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = round(correct / total, 4)
    
    per_class = {}
    weighted_prec = 0.0
    weighted_rec = 0.0
    weighted_f1 = 0.0
    
    for cls_name in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls_name and yp == cls_name)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls_name and yp == cls_name)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls_name and yp != cls_name)
        support = sum(1 for yt in y_true if yt == cls_name)
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        
        per_class[cls_name] = {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1_score": round(f1, 3),
            "support": support
        }
        
        weighted_prec += prec * (support / total)
        weighted_rec += rec * (support / total)
        weighted_f1 += f1 * (support / total)
        
    # Generate confusion matrix (rows = actual, cols = predicted)
    cm = [
        [sum(1 for yt, yp in zip(y_true, y_pred) if yt == row_cls and yp == col_cls) for col_cls in classes]
        for row_cls in classes
    ]
    
    return {
        "accuracy": accuracy,
        "weighted_precision": round(weighted_prec, 4),
        "weighted_recall": round(weighted_rec, 4),
        "weighted_f1_score": round(weighted_f1, 4),
        "per_class_metrics": per_class,
        "confusion_matrix": cm
    }
