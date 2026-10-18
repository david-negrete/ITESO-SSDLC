"""Apply a selected teaching change only inside a temporary GitHub test checkout."""
import os
from pathlib import Path

if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise SystemExit('This scenario only runs inside the temporary GitHub Actions checkout.')
scenario = os.environ.get('CLASSROOM_SCENARIO', 'authorization-regression')
if scenario == 'authorization-regression':
    path = Path('app.py')
    original = "if user['role'] != 'admin' and user['id'] != profile_id:"
    replacement = "if user['role'] != 'admin' and user['id'] != profile_id and profile_id == -1:"
elif scenario == 'validation-regression':
    path = Path('app.py')
    original = "if not isinstance(payload['bio'], str) or len(payload['bio']) > 200:"
    replacement = "if not isinstance(payload['bio'], str):"
elif scenario == 'csrf-test-setup-error':
    path = Path('tests/test_security.py')
    original = "self.send('/api/profiles/1', 'PATCH', {'bio': 'Updated'}).status_code"
    replacement = "self.send('/api/profiles/1', 'PATCH', {'bio': 'Updated'}, csrf=False).status_code"
elif scenario == 'logout-revocation-regression':
    path = Path('app.py')
    original = "    def logout():\n        with lock:\n            active_sessions.pop(session.get('sid'), None)\n        session.clear()"
    replacement = "    def logout():\n        # Teaching mutation: retain the backend session record.\n        session.clear()"
elif scenario == 'session-expiration-regression':
    path = Path('app.py')
    original = "if not record or record['expires'] <= time.monotonic():"
    replacement = "if not record:"
elif scenario == 'session-rotation-regression':
    path = Path('app.py')
    original = "            active_sessions.pop(session.get('sid'), None)\n            for token in list(active_sessions):"
    replacement = "            # Teaching mutation: retain the previous authenticated session.\n            for token in list(active_sessions):"
elif scenario == 'protected-field-regression':
    path = Path('app.py')
    original = "set(payload) - {'bio'}"
    replacement = "set(payload) - {'bio', 'role'}"
elif scenario == 'admin-access-regression':
    path = Path('app.py')
    original = "if user['role'] != 'admin' and user['id'] != profile_id:"
    replacement = "if user['id'] != profile_id:"
elif scenario == 'cache-policy-regression':
    path = Path('app.py')
    original = "response.headers['Cache-Control'] = 'no-store'"
    replacement = "response.headers['Cache-Control'] = 'public, max-age=3600'"
else:
    raise SystemExit('Unknown teaching scenario; no files changed.')
source = path.read_text(encoding='utf-8')
if source.count(original) != 1:
    raise SystemExit('Expected teaching target changed; update the scenario before running it.')
path.write_text(source.replace(original, replacement), encoding='utf-8')
print(f'Teaching scenario: {scenario}; changed only {path} in this temporary test checkout.')
