import sys
import json
import os
import hashlib
import time
from datetime import datetime
import pickle
import pandas as pd

def generate_dossier(tx_data, risk_score, feature_dict):
    dossier_id = f"DOS-{int(time.time())}-{hashlib.md5(str(tx_data).encode()).hexdigest()[:6].upper()}"
    
    amount = tx_data.get('amount', 0)
    turn_count = tx_data.get('turn_count', 1)
    prompt = tx_data.get('prompt', '')
    recipient = tx_data.get('recipient', 'Unknown Merchant / User')
    
    # Explainable Reason Codes
    reasons = []
    if risk_score >= 0.70:
        decision = "AUTO_BLOCKED"
        risk_level = "CRITICAL_FRAUD"
    elif risk_score >= 0.35:
        decision = "STEP_UP_CHALLENGE"
        risk_level = "ELEVATED_RISK"
    else:
        decision = "ALLOW"
        risk_level = "LEGITIMATE"

    if feature_dict.get('rebuff_heuristic_score', 0) > 0.4:
        reasons.append(f"Prompt injection pattern detected (Heuristic score: {feature_dict['rebuff_heuristic_score']:.2f})")
    if feature_dict.get('rebuff_llm_score', 0) > 0.5:
        reasons.append(f"Semantic intent anomaly detected by LLM guardrail (Score: {feature_dict['rebuff_llm_score']:.2f})")
    if amount > 2500:
        reasons.append(f"High-value anomalous transfer amount (INR {amount:,} exceeds baseline)")
    if turn_count > 3:
        reasons.append(f"Multi-turn social engineering velocity pattern (Turn count: {turn_count})")
    if not reasons:
        reasons.append("Signals within baseline commercial activity boundaries")

    # Cryptographic audit hash
    audit_payload = f"{dossier_id}:{amount}:{risk_score}:{datetime.utcnow().isoformat()}"
    evidence_hash = hashlib.sha256(audit_payload.encode()).hexdigest()

    # Formal representment statement for bank/gateway dispute defense
    representment = (
        f"DISPUTE DEFENSE STATEMENT — {dossier_id}\n"
        f"Merchant Protection Layer: SentinelRisk AI\n"
        f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Transaction Amount: INR {amount}\n"
        f"Risk Score: {risk_score:.4f} ({risk_level})\n"
        f"Enforced Action: {decision}\n"
        f"Primary Reason Codes:\n" + "\n".join([f"  - {r}" for r in reasons]) + "\n"
        f"Verification Digest: SHA256:{evidence_hash[:32]}...\n"
        f"Recommendation: Uphold merchant protection policy under NPCI/gateway fraud mitigation guidelines."
    )

    dossier = {
        "dossier_id": dossier_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "merchant_id": "MERCHANT_JUICE_SHOP_IN",
        "transaction": {
            "amount": amount,
            "currency": "INR",
            "turn_count": turn_count,
            "recipient": recipient,
            "prompt_sample": prompt[:120] if prompt else "N/A"
        },
        "risk_assessment": {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "decision": decision,
            "reasons": reasons
        },
        "telemetry": feature_dict,
        "evidence_pack": {
            "evidence_hash": evidence_hash,
            "representment_statement": representment
        }
    }
    return dossier

def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] != '-':
            raw_input = sys.argv[1]
        else:
            raw_input = sys.stdin.read()
            
        raw_input = raw_input.strip()
        if (raw_input.startswith("'") and raw_input.endswith("'")) or (raw_input.startswith('"') and raw_input.endswith('"')):
            if not raw_input.startswith('{"'):
                raw_input = raw_input[1:-1]
        
        # Handle powershell escaped quotes if present
        if '\\"' in raw_input and '\"' not in raw_input:
            raw_input = raw_input.replace('\\"', '"')

        try:
            payload = json.loads(raw_input)
        except Exception:
            # Fallback attempt if double escaped
            payload = json.loads(raw_input.replace('\\"', '"'))
        
        # Load classifier
        model_path = os.path.join(os.path.dirname(__file__), 'model', 'fraud_detector.pkl')
        with open(model_path, 'rb') as f:
            clf = pickle.load(f)

        features = ['turn_count', 'amount', 'rebuff_heuristic_score', 'rebuff_similarity_score', 'rebuff_llm_score']
        
        feature_dict = {
            'turn_count': int(payload.get('turn_count', 1)),
            'amount': float(payload.get('amount', 0)),
            'rebuff_heuristic_score': float(payload.get('rebuff_heuristic_score', 0.0)),
            'rebuff_similarity_score': float(payload.get('rebuff_similarity_score', 0.0)),
            'rebuff_llm_score': float(payload.get('rebuff_llm_score', 0.0))
        }

        df = pd.DataFrame([feature_dict])[features]
        risk_score = float(clf.predict_proba(df)[0][1])

        dossier = generate_dossier(payload, risk_score, feature_dict)
        
        # Save to dossier history file
        history_path = os.path.join(os.path.dirname(__file__), 'model', 'dossiers.json')
        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        history.insert(0, dossier)
        # Keep latest 50 dossiers
        history = history[:50]
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)

        print(json.dumps({
            "status": "success",
            "risk_score": round(risk_score, 4),
            "dossier": dossier
        }))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
