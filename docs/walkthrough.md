# Solution Walkthrough
## Mastercard Innovation Challenge 2026 — AI Defense Lab for Payment Security

---

## Executive Summary

We built a closed-loop red-team / blue-team AI system integrated into a forked OWASP Juice Shop instance. The system **identifies** 15 novel GenAI-powered payment fraud attacks, **generates** realistic simulations using a real LLM (Groq/Llama 3.1) with attack-specific scenarios, and **defends** them with a three-layer detection stack. The attacks discovered through simulation directly feed the training data for the defense model — closing the loop.

---

## Pillar 1: IDENTIFY — Attack Discovery

We mapped the emerging GenAI payment fraud landscape into **15 distinct attack vectors** across three categories, each grounded in how real payment systems and LLM agents work.

### Attack Taxonomy (15 Attacks)

**A. Agentic / LLM-Specific Attacks (6)**

| ID | Attack | Core Mechanism |
|---|---|---|
| ATK-001 | Prompt injection via merchant content | Malicious instructions hidden in receipts/tool output ingested by the banking agent |
| ATK-002 | Indirect injection from email/SMS | Agent reads external messages and executes attacker commands |
| ATK-003 | Tool-call parameter tampering | LLM is coerced to substitute attacker payee/amount into `transferFunds` arguments |
| ATK-004 | Role / system-instruction override | Claims of "authorized override" or "compliance mandate" to supersede system prompt |
| ATK-005 | Context-window poisoning | Benign details planted early in conversation, weaponized in later turn |
| ATK-006 | Data exfiltration via model output | Coax model to reveal PII, account data, or system prompt contents |

**B. Social Engineering Amplified by GenAI (4)**

| ID | Attack | Core Mechanism |
|---|---|---|
| ATK-007 | Multi-turn trust poisoning | Rapport building (advisor/vendor/romance persona) followed by urgent transfer request |
| ATK-008 | Executive / relative impersonation | GenAI-cloned writing style mimics CEO or family member demanding urgent transfer |
| ATK-009 | Deepfake voice callback fraud | Voice-cloned confirmation bypasses voice-2FA channel |
| ATK-010 | Synthetic identity / KYC forgery | GenAI-generated documents and selfies pass automated KYC |

**C. Business Logic Attacks (5)**

| ID | Attack | Core Mechanism |
|---|---|---|
| ATK-011 | Refund rerouting | Legitimate purchase + manipulated refund destination to attacker account |
| ATK-012 | New-payee fast-follow | Add payee then immediately transfer before cooling-off controls trigger |
| ATK-013 | Velocity shaping / smurfing | Many sub-threshold transfers collectively launder large sums |
| ATK-014 | Chargeback narrative generation | GenAI-crafted internally consistent false dispute evidence |
| ATK-015 | Mule network choreography | AI-optimised multi-hop transfer graph obfuscates laundering trail |

Taxonomy stored in: `identify/attack_taxonomy.json` (JSON with fields: `attack_id`, `name`, `category`, `channel`, `severity`, `preconditions`, `signals`, `defenses`, `simulation_recipe`, `mitre_atlas`)

---

## Pillar 2: GENERATE — Attack Simulation

### 2.1 Synthetic Training Dataset

**Script:** `generate/data_builder.py`  
**Output:** `generate/data/train.jsonl` — 1,200 rows

Each row represents a transaction attempt with features extracted from the agentic banking pipeline:

| Feature | Description |
|---|---|
| `turn_count` | Number of conversation turns (higher → multi-turn attacks) |
| `amount` | Transaction amount in JWC |
| `rebuff_heuristic_score` | Regex-based injection signal (0–1) |
| `rebuff_similarity_score` | Jaccard similarity to known injection phrases (0–1) |
| `rebuff_llm_score` | Secondary LLM injection classifier score (0–1) |
| `label` | 0 = legitimate, 1 = fraud/attack |
| `attack_type` | Which of the 10 simulated attack categories |

The dataset covers **10 distinct attack distributions** (ATK-001 through ATK-013), each with realistic feature ranges derived from how those attacks actually behave — for example, ATK-007 (trust poisoning) has deliberately low early Rebuff scores and high turn counts to model the gradual nature of the attack.

**Class distribution:** 800 fraud, 400 legitimate (balanced with `class_weight='balanced'` in training)

### 2.2 Live LLM Simulations

We built **5 interactive simulation pages** wired to the real Groq/Llama 3.1 API:

| Page URL | Attack(s) Simulated | System Prompt Variant |
|---|---|---|
| `/#/agentic-banking` | ATK-001, 003, 004, 006 | Ledger banking agent (standard) |
| `/#/attack-sim/indirect-injection` | ATK-002 | MailAssist — reads and acts on emails |
| `/#/attack-sim/trust-poisoning` | ATK-005, 007, 008 | Ledger with multi-turn memory |
| `/#/attack-sim/refund-rerouting` | ATK-011 | RefundBot — processes dispute claims |
| `/#/attack-sim/fast-follow` | ATK-012 | Ledger with new-payee cooling-off |

Each page:
- Accepts **natural language prompts** from the user
- Routes to the **real LLM** (Groq API) with an attack-appropriate system prompt that makes the agent behave like a vulnerable banking assistant
- Shows the **hidden attack payload** injected alongside each turn
- Displays **live Rebuff scores** and **ML fraud verdict** in the UI

### 2.3 Promptfoo Red-Team Suite

**File:** `redteam/injection.yaml` — **12 automated test cases**

We implemented **Promptfoo** to create deterministic, repeatable evaluation suites for our agentic endpoints. Instead of manual testing, Promptfoo runs a custom provider (`ledgerProvider.cjs`) that simulates API interactions against our banking backend. 

Each test case evaluates the defense using robust assertions:
- **`javascript` assertions**: Validates that the agent selected the correct tool (e.g., `transferFunds` vs `getBalance`) and that the tool arguments were not tampered with.
- **`contains` assertions**: Ensures the final LLM output correctly enforces the policy gate (e.g., ensuring it returns "blocked by security policy").

It covers: direct override (ATK-001), system prompt leak (ATK-006), email injection (ATK-002), compliance authority (ATK-004), memo field tampering (ATK-003), CEO impersonation (ATK-008), new-payee fast-follow (ATK-012), context poisoning (ATK-005), velocity shaping (ATK-013), and 3 legitimate baselines.

```powershell
npm run redteam   # runs the full suite
```

### 2.4 Garak Integration for Novel Fuzzing (Research)

While Promptfoo handles deterministic regression testing, our architecture is designed to integrate with **Garak** (LLM vulnerability scanner) to discover novel, unforeseen attack variations. By pointing Garak at our `/rest/attack-sim` endpoint, we can fuzz the agent with thousands of generated prompt variations (using techniques like adversarial suffixes or tree-of-attacks). 

When Garak discovers a successful bypass, we extract those attack patterns and feed them back into the `generate/data_builder.py` script to retrain the LightGBM defense classifier. This creates an automated immune system that hardens against zero-day GenAI threats.

---

## Pillar 3: DEFEND — Detection and Mitigation

### 3.1 Three-Layer Defense Stack

```
User Input → [Layer 1: Rebuff 3-Signal] → LLM Agent → [Layer 2: ML Classifier] → Decision
                                                                 ↓
                                                    [Layer 3: Policy Gate]
```

**Layer 1 — Rebuff-Compatible Signal Detector** (`lib/rebuffSignal.ts`)

Runs on every incoming message before it reaches the LLM:
- **Heuristic score**: 4 regex patterns for `(ignore|override|bypass)` verbs and `(reveal|leak)` intent
- **Vector similarity**: Jaccard distance against 6 canonical injection phrases
- **LLM score**: Secondary model classifies injection probability 0–1

Inspired by the Rebuff framework (forked at `../rebuff`) and reimplemented in TypeScript within Juice Shop's Express server.

**Layer 2 — LightGBM Fraud Classifier** (`defend/`)

Trained on 1,200 synthetic examples using the 5-feature vector. Runs after every `transferFunds` tool call via a Python subprocess (`defend/infer.py`).

**Evaluation Results (on 20% held-out test set):**

| Metric | Score |
|---|---|
| **ROC-AUC** | **0.9994** |
| **F1 Score** | **0.9938** |
| **Precision** | **0.9938** |
| **Recall** | **0.9938** |
| Accuracy | 0.99 |

The model achieves near-perfect discrimination because each attack type has distinctive feature distributions — particularly the combination of `rebuff_heuristic_score` and `turn_count` separates agentic attacks (high heuristic, low turn count) from social engineering attacks (low heuristic, high turn count).

**Layer 3 — Policy Gate** (server-side enforcement in `routes/agenticBanking.ts` and `routes/attackSim.ts`)

Hard rules that cannot be bypassed by LLM output:
- All transfers require explicit user confirmation (`yes`/`confirm` in the same message)
- New payees have a 60-second cooling-off period before first transfer (ATK-012)
- Refund destination is server-pinned to original payment source (ATK-011)
- `LEDGER_VULNERABLE_REROUTE=true` enables ATK-003 destination tampering demo

### 3.2 Defense Modes

| Mode | Behavior | Env Variable |
|---|---|---|
| `observe` (default) | Scores every transaction, logs risk, never blocks | `LEDGER_DEFENSE_MODE=observe` |
| `enforce` | Blocks transfers above 0.80 risk threshold | `LEDGER_DEFENSE_MODE=enforce` |

### 3.3 Closed-Loop Feedback

The attacks generated in Pillar 2 become the training data for Pillar 3. Specifically:
1. The LLM simulations in `routes/agenticBanking.ts` log Rebuff signals per request
2. These signals feed `generate/data_builder.py`'s feature distributions
3. `defend/train.py` retrains from the updated dataset
4. The new model artifact replaces `defend/model/fraud_detector.pkl`
5. Future simulations run against the improved detector — gaps drive new attack ideas

---

## Real-World Feasibility

| Aspect | Implementation | Production Path |
|---|---|---|
| **Prompt injection defense** | Rebuff heuristic + LLM classifier, runs in <5ms | Deploy as API middleware in payment processing stack |
| **ML model** | LightGBM, 5 features, real-time inference via subprocess | Compile to ONNX or wrap as microservice for <10ms latency |
| **Policy gate** | Stateless server-side rules | Integrate with existing fraud rule engine |
| **LLM agent** | Groq/Llama 3.1 via AI SDK Vercel | Swap to any OpenAI-compatible provider; model is swappable |
| **Red-team suite** | Promptfoo YAML, runs in CI | Schedule nightly against staging with regression alerts |
| **Attack taxonomy** | JSON, 15 entries, MITRE ATLAs references | Extend to full MITRE ATLAs mapping, share with industry ISAC |

---

## How to Run

```powershell
# 1. Install
npm install
pip install lightgbm scikit-learn pandas

# 2. Set API key
$env:LLM_API_KEY = "gsk_your_groq_key"
$env:NODE_CONFIG = '{"application":{"chatBot":{"llmApiUrl":"https://api.groq.com/openai/v1","model":"llama-3.1-8b-instant","llmMaxRetries":2}}}'

# 3. Train ML model
python generate/data_builder.py
python defend/train.py

# 4. Start server
npm start

# 5. Open demo
# http://localhost:3000/#/attack-hub
```

---

## Conclusion

This solution demonstrates that fighting GenAI fraud requires GenAI defenses. By owning the full cycle — identifying attack vectors, generating realistic simulations with a live LLM, and defending with a multi-layer detection stack — we create a system where every new attack discovered immediately strengthens the defense. The closed-loop architecture makes the solution progressively harder to evade over time.
