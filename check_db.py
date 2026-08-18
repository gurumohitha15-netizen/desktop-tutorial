import sqlite3
import json

conn = sqlite3.connect('instance/app.db')
conn.row_factory = sqlite3.Row

print("=== USERS ===")
for r in conn.execute("SELECT * FROM users").fetchall():
    print(dict(r))

print("\n=== INTEREST PROFILES ===")
for r in conn.execute("SELECT * FROM interest_profiles").fetchall():
    p = dict(r)
    p['secondary_interests'] = json.loads(p['secondary_interests'])
    p['interest_scores'] = json.loads(p['interest_scores'])
    print(p)

print("\n=== INTERACTIONS COUNT ===")
print(conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0])

print("\n=== RECOMMENDATIONS COUNT ===")
print(conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0])

conn.close()
