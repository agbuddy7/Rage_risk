# SentinelRisk: Enterprise AI Risk Manager & Loss Prevention System

> **Hackathon Submission Track**: AI Risk Manager  
> **Target Class of Loss**: Merchant Payment Fraud, Agentic Transfer Hijacks & Return/Chargeback Abuse  
> **Core Innovation**: Bounded Defense-Only Risk Engine with Quantified False-Positive Customer Friction Optimization ($FP \times C_{friction} + FN \times C_{fraud}$) and Automated Dispute Dossier Representment.

---

## 1. Executive Summary

As GenAI agents and autonomous buyer bots enter modern digital commerce, merchants face a dual existential crisis:
1. **Agentic Payment Hijacking & Social Engineering Fraud**: Malicious actors use prompt injection, role overrides, and multi-turn context poisoning to trick banking/checkout agents into unauthorized funds transfers and automated drain attacks.
2. **False-Positive Margin Destruction**: Traditional rule engines and over-sensitive classifiers aggressively block transactions. Insulting a legitimate customer costs $30–$50 in lost lifetime value, support tickets, and checkout abandonment.

**SentinelRisk** solves this by delivering an enterprise **defense-only** AI Risk Management platform integrated directly into an e-commerce storefront (OWASP Juice Shop). It combines a cost-sensitive **LightGBM fraud classifier**, **multi-layered heuristic guardrails (Rebuff)**, an interactive **Held-Out Test Benchmark**, and an **Auto-Responder Evidence Pack Generator** that auto-assembles audit-ready dispute dossiers.

---

## 2. Meeting "The Bar"

| The Hackathon Bar | SentinelRisk Implementation | Proof Point |
|---|---|---|
| **One Class of Loss** | Merchant Payment Fraud, ATO & Refund Abuse | Evaluated across 240 held-out transactions with 6 distinct attack vectors. |
| **Working Detector & Verifier** | Dual-layer LightGBM + Rebuff Heuristic Engine | Scores risk in $<20\text{ms}$ with real-time SHAP-inspired explainability. |
| **Measured Precision & Recall on Held-Out Set** | 20% Held-Out Split (240 records: 80 Legit, 160 Fraud) | **Precision: 99.38%**, **Recall: 99.38%**, **ROC-AUC: 0.9994**, **F1: 0.9938**. |
| **Honest Metrics: False-Positive Cost** | Quantified Cost Function: $(FP \times ₹350) + (FN \times ₹3,450)$ | Proves cost-optimal operating threshold ($\tau^* = 0.05 - 0.10$) saves ₹5,48,200 (99.31% net loss reduction). |
| **Strictly Defense-Only** | Auto-Responder Dossier Generator | Produces immutable audit trails, cryptographic SHA256 digests, and formal representment statements. |

---

## 3. Held-Out Test Set Performance

Our held-out benchmark ($N = 240$) demonstrates near-perfect discrimination between genuine customer purchases and adversarial attacks:

### Confusion Matrix

| | **Predicted Legitimate** | **Predicted Fraud** |
|---|:---:|:---:|
| **Actual Legitimate** | **79 (TN)** *(Passed with zero friction)* | **1 (FP)** *(Friction cost: ₹350)* |
| **Actual Fraud** | **1 (FN)** *(Direct loss: ₹3,450)* | **159 (TP)** *(Attacks blocked & defended)* |

### Performance Summary
* **Accuracy**: 99.17%
* **Precision**: 99.38%
* **Recall**: 99.38%
* **F1 Score**: 99.38%
* **ROC-AUC**: 0.9994

---

## 4. Quantified False-Positive Cost Analysis

Traditional fraud detectors optimize raw accuracy, resulting in high false-positive rates that infuriate good customers. SentinelRisk uses an explicit **Cost Function**:

$$\text{Financial Loss}(\tau) = \Big(FP(\tau) \times C_{friction}\Big) + \Big(FN(\tau) \times C_{fraud}\Big)$$

Where:
* $C_{friction} = ₹350$: Cost of customer friction (OTP step-up drop-off, support verification, cart abandonment).
* $C_{fraud} = ₹3,450$: Average direct merchant loss per undetected fraudulent transaction (chargeback fees + product loss).

### Cost-Benefit Across Operating Thresholds ($\tau$)

| Threshold ($\tau$) | Precision | Recall | False Positives ($FP$) | False Negatives ($FN$) | Total Cost (INR) | Net Merchant Savings |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0.05 (Optimal)** | **98.16%** | **100.0%** | **3** | **0** | **₹1,050** | **₹5,50,950 (99.81%)** |
| **0.10** | **99.38%** | **99.38%** | **1** | **1** | **₹3,800** | **₹5,48,200 (99.31%)** |
| **0.50 (Default)** | **99.38%** | **99.38%** | **1** | **1** | **₹3,800** | **₹5,48,200 (99.31%)** |
| **0.85** | 99.36% | 98.12% | 1 | 3 | ₹10,700 | ₹5,41,300 (98.06%) |
| **0.95 (Permissive)**| 100.0% | 85.00% | 0 | 24 | ₹82,800 | ₹4,69,200 (85.00%) |

---

## 5. Defense Auto-Responder & Dispute Representment

When risk is flagged or a dispute is registered, SentinelRisk’s **Auto-Responder** compiles an audit-ready dossier:

1. **Transaction Telemetry**: Velocity, amount, session turn count, and payment channel.
2. **Explainable Reason Codes**: Human-interpretable flags (e.g., *"Multi-turn social engineering velocity pattern (Turn count: 4)"*, *"Prompt injection pattern detected"*).
3. **Cryptographic Proof**: SHA256 verification digest guaranteeing evidence integrity.
4. **Automated Gateway Representment**: Pre-formatted formal defense statement complying with NPCI and payment gateway dispute adjudication guidelines.

---

## 6. How to Run & Verify

1. **Train Model & Compute Held-Out Metrics**:
   ```bash
   python defend/train.py
   ```
2. **Launch Application**:
   ```bash
   npm start
   ```
3. **Open AI Risk Manager Console**:
   Navigate to: `http://localhost:3000/#/risk-manager`
   * Click **"Test Presets"** in Tab 1 to see real-time risk decisioning and auto-responder dossiers.
   * Slide the **Decision Threshold** in Tab 2 to visualize the live trade-off between customer friction and fraud leakage.
   * Inspect generated defense dossiers in Tab 3.
