# AI Defense Lab for Payment Security
### Mastercard Innovation Challenge 2026 · GFF Mumbai

> **Build the attack. Build the defense. Close the loop.**

This repository implements a closed-loop red-team / blue-team AI system for GenAI-powered payment fraud — built on top of a forked [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) as the vulnerable payment target.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREE PILLARS                                 │
│                                                                  │
│  IDENTIFY          GENERATE           DEFEND                     │
│  ─────────         ────────           ──────                     │
│  15 attack         Synthetic data     LightGBM classifier        │
│  taxonomy          generator          + Rebuff-compatible        │
│  (JSON)            (1200 rows)        3-signal detector          │
│                    + LLM payloads     + policy gate              │
└─────────────────────────────────────────────────────────────────┘
         ↑                                         │
         └──── Closed-loop feedback (retrain) ─────┘
```

---

## Quick Start

### Prerequisites
- Node.js ≥ 20, npm ≥ 10
- Python ≥ 3.10 with `lightgbm`, `scikit-learn`, `pandas`
- A Groq API key (free tier works): https://console.groq.com

### 1. Install dependencies
```powershell
npm install
pip install lightgbm scikit-learn pandas
```

### 2. Set environment variables
```powershell
$env:LLM_API_KEY = "gsk_your_groq_key_here"
$env:NODE_CONFIG = '{"application":{"chatBot":{"llmApiUrl":"https://api.groq.com/openai/v1","model":"llama-3.1-8b-instant","llmMaxRetries":2}}}'
```

### 3. Generate training data & train ML model
```powershell
python generate/data_builder.py   # generates 1200-row JSONL dataset
python defend/train.py            # trains LightGBM, saves model + metrics
```

### 4. Start the server
```powershell
npm start
```

### 5. Open the demo
Navigate to: **http://localhost:3000/#/attack-hub**

---

## Project Structure

```
juice-shop/
├── identify/
│   └── attack_taxonomy.json    # 15 GenAI payment fraud attacks
├── generate/
│   ├── data_builder.py         # Synthetic dataset generator (1200 rows, 10 attack types)
│   └── data/train.jsonl        # Generated training data
├── defend/
│   ├── train.py                # LightGBM training (ROC-AUC, F1, Precision, Recall)
│   ├── infer.py                # Real-time inference called per transaction
│   └── model/
│       ├── fraud_detector.pkl  # Trained model artifact
│       └── metrics.json        # Evaluation results
├── redteam/
│   ├── injection.yaml          # 12 Promptfoo adversarial test cases
│   ├── legitimate.yaml         # Baseline legitimate scenarios
│   ├── ledgerProvider.cjs      # Custom Promptfoo provider
│   └── README.md               # Red-team suite docs
├── routes/
│   ├── agenticBanking.ts       # ATK-001/003/004/006: Ledger banking agent
│   └── attackSim.ts            # ATK-002/007/011/012: Shared attack sim route
├── lib/
│   └── rebuffSignal.ts         # Rebuff-compatible 3-signal detector
└── frontend/src/app/
    ├── attack-hub/             # 15-attack scenario hub dashboard
    ├── attack-sim/
    │   ├── indirect-injection/ # ATK-002: Email/SMS injection sim
    │   ├── trust-poisoning/    # ATK-007: Multi-turn trust poisoning sim
    │   ├── refund-rerouting/   # ATK-011: Refund destination tampering sim
    │   └── fast-follow/        # ATK-012: New-payee fast-follow sim
    └── agentic-banking/        # ATK-001/003/004: Original Ledger agent
```

---

## Attack Coverage

| ID | Attack Name | Category | Severity | Simulated |
|---|---|---|---|---|
| ATK-001 | Prompt injection via merchant content | Agentic/LLM | 🔴 Critical | ✅ |
| ATK-002 | Indirect injection from email/SMS | Agentic/LLM | 🔴 Critical | ✅ |
| ATK-003 | Tool-call parameter tampering | Agentic/LLM | 🔴 Critical | ✅ |
| ATK-004 | Role/system-instruction override | Agentic/LLM | 🟠 High | ✅ |
| ATK-005 | Context-window poisoning | Agentic/LLM | 🟠 High | ✅ |
| ATK-006 | Data exfiltration via model output | Agentic/LLM | 🟠 High | ✅ |
| ATK-007 | Multi-turn trust poisoning | Social Eng. | 🔴 Critical | ✅ |
| ATK-008 | Executive/relative impersonation | Social Eng. | 🟠 High | ✅ |
| ATK-009 | Deepfake voice callback fraud | Social Eng. | 🟠 High | 📄 Research |
| ATK-010 | Synthetic identity/KYC forgery | Social Eng. | 🟠 High | 📄 Research |
| ATK-011 | Refund rerouting to attacker account | Business Logic | 🟠 High | ✅ |
| ATK-012 | New-payee fast-follow transfer abuse | Business Logic | 🟠 High | ✅ |
| ATK-013 | Velocity shaping / smurfing | Business Logic | 🟡 Medium | ✅ |
| ATK-014 | Chargeback narrative generation | Business Logic | 🟡 Medium | 📄 Research |
| ATK-015 | Mule network choreography | Business Logic | 🟡 Medium | 📄 Research |

---

## Defense Layers

### Layer 1: Rebuff-Compatible 3-Signal Detector (`lib/rebuffSignal.ts`)
Every user message is scored across three signals before reaching the LLM:
- **Heuristic score**: Regex patterns for override verbs, authority claims, reveal instructions
- **Vector similarity**: Jaccard similarity against 6 known injection example phrases
- **LLM classifier score**: Secondary LLM rates injection probability 0–1

### Layer 2: ML Fraud Classifier (`defend/`)
A LightGBM classifier trained on 1200 synthetic examples (10 attack types) using features:
- `turn_count`, `amount`, `rebuff_heuristic_score`, `rebuff_similarity_score`, `rebuff_llm_score`

Operates in two modes via `LEDGER_DEFENSE_MODE`:
- **`observe`** (default): Logs scores, does not block
- **`enforce`**: Blocks transfers above `LEDGER_MODEL_THRESHOLD_HIGH` (default 0.80)

### Layer 3: Policy Gate
- Transfers require explicit user confirmation (`yes`/`confirm`)
- New-payee 60-second cooling-off period (ATK-012)
- Refund destination pinned to original source (ATK-011)
- Tool argument pinning: server validates agent-chosen args vs user intent

---

## Red-Team Suite & Fuzzing (Promptfoo + Garak)

### Promptfoo: Deterministic Regression Testing
We implemented **Promptfoo** to create deterministic, repeatable evaluation suites for our agentic endpoints. Instead of manual testing, Promptfoo runs a custom provider (`ledgerProvider.cjs`) that simulates API interactions against our banking backend. 

Each test case evaluates the defense using robust assertions:
- **`javascript` assertions**: Validates that the agent selected the correct tool (e.g., `transferFunds` vs `getBalance`) and that the tool arguments were not tampered with.
- **`contains` assertions**: Ensures the final LLM output correctly enforces the policy gate (e.g., ensuring it returns "blocked by security policy").

```powershell
# Run Promptfoo adversarial test suite (12 scenarios)
npm run redteam
```

It covers: direct override (ATK-001), system prompt leak (ATK-006), email injection (ATK-002), compliance authority (ATK-004), memo field tampering (ATK-003), CEO impersonation (ATK-008), new-payee fast-follow (ATK-012), context poisoning (ATK-005), velocity shaping (ATK-013), and 3 legitimate baselines.

### Garak Integration: Novel Fuzzing (Research)
While Promptfoo handles deterministic testing, our architecture is designed to integrate with **Garak** (LLM vulnerability scanner) to discover novel, unforeseen attack variations. By pointing Garak at our `/rest/attack-sim` endpoint, we can fuzz the agent with thousands of generated prompt variations (using techniques like adversarial suffixes or tree-of-attacks). 

When Garak discovers a successful bypass, we extract those attack patterns and feed them back into the `generate/data_builder.py` script to retrain the LightGBM defense classifier. This creates an automated immune system that hardens against zero-day GenAI threats.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_API_KEY` | — | Groq/OpenAI API key |
| `LEDGER_DEFENSE_MODE` | `observe` | `observe` or `enforce` |
| `LEDGER_MODEL_THRESHOLD_HIGH` | `0.80` | Block threshold |
| `LEDGER_MODEL_THRESHOLD_MED` | `0.60` | Step-up threshold |
| `LEDGER_VULNERABLE_REROUTE` | `false` | Enable ATK-003 demonstration |
| `LEDGER_ATTACKER_DESTINATION` | `attacker-controlled-sink` | Reroute target when vulnerable |

---

## Contributors
Built for Mastercard Innovation Challenge @ GFF 2026
