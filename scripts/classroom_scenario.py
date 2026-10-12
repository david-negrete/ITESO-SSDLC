"""Apply a deliberate regression only inside an ephemeral GitHub test checkout."""
import os
from pathlib import Path

if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise SystemExit('This scenario only runs inside the temporary GitHub Actions checkout.')
path = Path('app.py')
source = path.read_text(encoding='utf-8')
original = "if user['role'] != 'admin' and user['id'] != profile_id:"
replacement = "if user['role'] != 'admin' and user['id'] != profile_id and profile_id == -1:"
if source.count(original) != 1:
    raise SystemExit('Authorization check changed; update the classroom scenario before running it.')
path.write_text(source.replace(original, replacement), encoding='utf-8')
print('Teaching scenario: object ownership enforcement removed in this temporary test checkout.')
