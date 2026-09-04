import json
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
import lightgbm as lgb

def train():
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generate', 'data', 'train.jsonl')
    df = pd.read_json(data_path, lines=True)

    features = ['turn_count', 'amount', 'rebuff_heuristic_score', 'rebuff_similarity_score', 'rebuff_llm_score']
    X = df[features]
    y = df['label']
    attack_types = df.get('attack_type', pd.Series(['unknown'] * len(df)))

    # Split: 80% train, 20% held-out test set
    X_train, X_test, y_train, y_test, attack_train, attack_test = train_test_split(
        X, y, attack_types, test_size=0.2, random_state=42, stratify=y
    )

    clf = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        num_leaves=31,
        class_weight='balanced',
        random_state=42
    )
    clf.fit(X_train, y_train)

    probs = clf.predict_proba(X_test)[:, 1]
    preds_default = (probs >= 0.5).astype(int)

    auc   = float(roc_auc_score(y_test, probs))
    f1    = float(f1_score(y_test, preds_default))
    prec  = float(precision_score(y_test, preds_default))
    rec   = float(recall_score(y_test, preds_default))

    cm = confusion_matrix(y_test, preds_default)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    # Cost-Sensitive Optimization
    # Unit cost of FP (customer friction / OTP step-up / cart friction): ₹350
    # Unit cost of FN (direct chargeback / refund loss / unrecovered money): ₹3450
    cost_fp = 350
    cost_fn = 3450

    threshold_sweep = []
    best_threshold = 0.5
    min_cost = float('inf')

    for t in np.linspace(0.05, 0.95, 19):
        p_t = (probs >= t).astype(int)
        c_matrix = confusion_matrix(y_test, p_t)
        t_tn, t_fp, t_fn, t_tp = [int(v) for v in c_matrix.ravel()]
        
        t_prec = float(precision_score(y_test, p_t, zero_division=0))
        t_rec = float(recall_score(y_test, p_t, zero_division=0))
        t_f1 = float(f1_score(y_test, p_t, zero_division=0))
        
        # Financial cost = FP friction + FN fraud leakage
        financial_cost = (t_fp * cost_fp) + (t_fn * cost_fn)
        potential_loss = (t_tp + t_fn) * cost_fn
        net_savings = potential_loss - financial_cost

        threshold_sweep.append({
            "threshold": round(float(t), 2),
            "precision": round(t_prec, 4),
            "recall": round(t_rec, 4),
            "f1": round(t_f1, 4),
            "tn": t_tn,
            "fp": t_fp,
            "fn": t_fn,
            "tp": t_tp,
            "financial_cost_inr": financial_cost,
            "net_savings_inr": net_savings
        })

        if financial_cost < min_cost:
            min_cost = financial_cost
            best_threshold = round(float(t), 2)

    # Per-attack recall breakdown
    attack_breakdown = {}
    for atype in attack_test.unique():
        if atype == 'none':
            continue
        mask = (attack_test == atype)
        if mask.sum() > 0:
            atype_rec = float(recall_score(y_test[mask], preds_default[mask], zero_division=0))
            attack_breakdown[atype] = {
                "total_attempts": int(mask.sum()),
                "detected": int((preds_default[mask] == 1).sum()),
                "recall": round(atype_rec, 4)
            }

    # Feature Importance
    feature_importances = dict(zip(features, [float(v) for v in clf.feature_importances_]))

    total_potential_loss = (tp + fn) * cost_fn
    total_incurred_cost = (fp * cost_fp) + (fn * cost_fn)
    net_savings = total_potential_loss - total_incurred_cost

    metrics = {
        "benchmark_summary": {
            "track": "AI Risk Manager",
            "model": "LightGBM Cost-Sensitive Risk Classifier",
            "held_out_test_size": len(y_test),
            "legitimate_samples": int((y_test == 0).sum()),
            "fraud_samples": int((y_test == 1).sum()),
            "roc_auc": round(auc, 4),
            "f1": round(f1, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "accuracy": round(float((preds_default == y_test).mean()), 4)
        },
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp
        },
        "cost_analysis": {
            "unit_cost_fp_inr": cost_fp,
            "unit_cost_fn_inr": cost_fn,
            "total_potential_loss_inr": total_potential_loss,
            "total_incurred_cost_inr": total_incurred_cost,
            "net_merchant_savings_inr": net_savings,
            "loss_reduction_pct": round((net_savings / total_potential_loss) * 100, 2),
            "optimal_operating_threshold": best_threshold,
            "threshold_sweep": threshold_sweep
        },
        "attack_type_breakdown": attack_breakdown,
        "feature_importances": feature_importances
    }

    # Save model
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'fraud_detector.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)

    metrics_path = os.path.join(model_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print("=" * 60)
    print("AI RISK MANAGER — HELD-OUT TEST BENCHMARK")
    print("=" * 60)
    print(f"Held-Out Records : {len(y_test)} (Legit: {(y_test == 0).sum()}, Fraud: {(y_test == 1).sum()})")
    print(f"ROC-AUC          : {auc:.4f}")
    print(f"Precision        : {prec:.4f}")
    print(f"Recall           : {rec:.4f}")
    print(f"F1 Score         : {f1:.4f}")
    print(f"Confusion Matrix : TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"Net Savings      : INR {net_savings:,} ({metrics['cost_analysis']['loss_reduction_pct']}% reduction)")
    print(f"Optimal Threshold: {best_threshold}")
    print("=" * 60)
    print(f"Metrics saved to: {metrics_path}")

if __name__ == '__main__':
    train()
