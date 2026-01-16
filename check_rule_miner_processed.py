
import json
import os

try:
    with open('data/golden_rules.json', 'r', encoding='utf-8') as f:
        rules = json.load(f)
        docs = sorted(list({rule.get('source_doc') for rule in rules if rule.get('source_doc')}))
        print("Processed documents:")
        for doc in docs:
            print(f" - {doc}")
except Exception as e:
    print(f"Error: {e}")
