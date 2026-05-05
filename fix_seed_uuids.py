import uuid
import re

with open("scripts/seed_db.py", "r") as f:
    content = f.read()

ids_to_replace = {
    "usr-1": str(uuid.uuid4()),
    "usr-2": str(uuid.uuid4()),
    "usr-3": str(uuid.uuid4()),
    "usr-4": str(uuid.uuid4()),
    "frm-1": str(uuid.uuid4()),
    "cert-1": str(uuid.uuid4()),
    "prod-1": str(uuid.uuid4()),
    "prod-2": str(uuid.uuid4()),
    "vp-1": str(uuid.uuid4()),
    "vp-2": str(uuid.uuid4()),
    "ts-1": str(uuid.uuid4()),
}

for old, new in ids_to_replace.items():
    content = content.replace(f'"{old}"', f'"{new}"')

with open("scripts/seed_db.py", "w") as f:
    f.write(content)
print("Replaced UUIDs in seed_db.py!")
