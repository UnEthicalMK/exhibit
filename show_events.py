import json
import sqlite3

conn = sqlite3.connect("exhibit.db")
rows = conn.execute(
    "SELECT id, event_type, dispute_id, processed, raw FROM webhookevent"
).fetchall()
print(len(rows), "stored webhook event(s)")
for event_id, event_type, dispute_id, processed, raw in rows:
    event = json.loads(raw)
    resource = event.get("resource") or {}
    print("-", event_id, event_type, "| dispute_id:", dispute_id, "| processed:", processed)
    print("  summary:", event.get("summary"))
    print("  resource_type:", event.get("resource_type"))
    print("  resource keys:", sorted(resource.keys()))