import json, random, os

ATTACKS = [
    # (label, heuristic_range, vector_range, llm_range, amount_range, turn_range)
    # ATK-001: Prompt injection via merchant content
    {"label": 1, "h": (0.7, 1.0), "v": (0.55, 1.0), "l": (0.75, 1.0), "amt": (100, 5000), "t": (1, 2), "attack_type": "merchant_injection"},
    # ATK-002: Indirect injection from email/SMS
    {"label": 1, "h": (0.65, 1.0), "v": (0.5, 0.95), "l": (0.7, 1.0), "amt": (200, 4000), "t": (1, 2), "attack_type": "indirect_injection"},
    # ATK-003: Tool-call parameter tampering
    {"label": 1, "h": (0.5, 0.9), "v": (0.4, 0.9), "l": (0.6, 1.0), "amt": (500, 5000), "t": (1, 3), "attack_type": "param_tampering"},
    # ATK-004: Role/system override
    {"label": 1, "h": (0.8, 1.0), "v": (0.7, 1.0), "l": (0.85, 1.0), "amt": (1000, 5000), "t": (1, 2), "attack_type": "role_override"},
    # ATK-005: Context-window poisoning
    {"label": 1, "h": (0.2, 0.6), "v": (0.1, 0.5), "l": (0.3, 0.8), "amt": (500, 5000), "t": (4, 8), "attack_type": "context_poisoning"},
    # ATK-007: Multi-turn trust poisoning
    {"label": 1, "h": (0.1, 0.4), "v": (0.0, 0.3), "l": (0.2, 0.6), "amt": (800, 5000), "t": (4, 10), "attack_type": "trust_poisoning"},
    # ATK-008: Executive impersonation
    {"label": 1, "h": (0.6, 0.95), "v": (0.5, 0.9), "l": (0.7, 1.0), "amt": (1000, 5000), "t": (1, 3), "attack_type": "impersonation"},
    # ATK-011: Refund rerouting
    {"label": 1, "h": (0.3, 0.7), "v": (0.2, 0.6), "l": (0.4, 0.85), "amt": (50, 1000), "t": (2, 4), "attack_type": "refund_rerouting"},
    # ATK-012: New-payee fast-follow
    {"label": 1, "h": (0.0, 0.3), "v": (0.0, 0.2), "l": (0.0, 0.4), "amt": (400, 5000), "t": (2, 3), "attack_type": "fast_follow"},
    # ATK-013: Velocity shaping
    {"label": 1, "h": (0.0, 0.2), "v": (0.0, 0.15), "l": (0.0, 0.3), "amt": (90, 999), "t": (1, 2), "attack_type": "velocity_shaping"},
]

LEGITIMATE = [
    {"label": 0, "h": (0.0, 0.15), "v": (0.0, 0.1), "l": (0.0, 0.15), "amt": (5, 300), "t": (1, 4), "attack_type": "none"},
    {"label": 0, "h": (0.0, 0.2), "v": (0.0, 0.12), "l": (0.0, 0.18), "amt": (10, 500), "t": (1, 3), "attack_type": "none"},
    {"label": 0, "h": (0.0, 0.1), "v": (0.0, 0.08), "l": (0.0, 0.12), "amt": (20, 200), "t": (2, 6), "attack_type": "none"},
]

def generate_dataset(num_per_attack=80, num_legit=400):
    data = []

    for attack in ATTACKS:
        for _ in range(num_per_attack):
            row = {
                "turn_count": random.randint(attack["t"][0], attack["t"][1]),
                "amount": random.randint(attack["amt"][0], attack["amt"][1]),
                "rebuff_heuristic_score": round(random.uniform(attack["h"][0], attack["h"][1]), 4),
                "rebuff_similarity_score": round(random.uniform(attack["v"][0], attack["v"][1]), 4),
                "rebuff_llm_score": round(random.uniform(attack["l"][0], attack["l"][1]), 4),
                "label": attack["label"],
                "attack_type": attack["attack_type"]
            }
            data.append(row)

    legit_templates = LEGITIMATE * (num_legit // len(LEGITIMATE) + 1)
    for template in legit_templates[:num_legit]:
        row = {
            "turn_count": random.randint(template["t"][0], template["t"][1]),
            "amount": random.randint(template["amt"][0], template["amt"][1]),
            "rebuff_heuristic_score": round(random.uniform(template["h"][0], template["h"][1]), 4),
            "rebuff_similarity_score": round(random.uniform(template["v"][0], template["v"][1]), 4),
            "rebuff_llm_score": round(random.uniform(template["l"][0], template["l"][1]), 4),
            "label": template["label"],
            "attack_type": template["attack_type"]
        }
        data.append(row)

    random.shuffle(data)
    os.makedirs(os.path.dirname(os.path.abspath(__file__)) + '/data', exist_ok=True)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'train.jsonl')
    with open(out_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

    fraud_count = sum(1 for d in data if d["label"] == 1)
    legit_count = sum(1 for d in data if d["label"] == 0)
    print(f"Generated {len(data)} rows: {fraud_count} fraud, {legit_count} legitimate")
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    generate_dataset()
