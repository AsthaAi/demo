import os
import json

tracker_path = os.path.join(os.path.dirname(
    __file__), 'risk_demo_tracker.json')
data = {'__default__': True}
try:
    with open(tracker_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[TEST] Successfully wrote to {tracker_path}: {data}")
except Exception as e:
    print(f"[TEST] Failed to write to {tracker_path}: {e}")
