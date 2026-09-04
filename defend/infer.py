import sys
import json
import os
import pickle
import pandas as pd

def infer():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)
        
    try:
        input_data = json.loads(sys.argv[1])
        
        # Load model
        model_path = os.path.join(os.path.dirname(__file__), 'model', 'fraud_detector.pkl')
        with open(model_path, 'rb') as f:
            clf = pickle.load(f)
            
        features = ['turn_count', 'amount', 'rebuff_heuristic_score', 'rebuff_similarity_score', 'rebuff_llm_score']
        df = pd.DataFrame([input_data])[features]
        
        score = float(clf.predict_proba(df)[0][1])
        print(json.dumps({"score": score}))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    infer()
