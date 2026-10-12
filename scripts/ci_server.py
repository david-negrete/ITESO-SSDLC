"""Start an isolated loopback-only target with ephemeral credentials for ZAP."""
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

os.environ['APP_LOCAL_HTTP'] = '1'
os.environ['APP_SECRET_KEY'] = secrets.token_urlsafe(48)
for name in ('ALICE', 'BOB', 'ADMIN'):
    os.environ[f'{name}_PASSWORD'] = secrets.token_urlsafe(24)
create_app().run(host='127.0.0.1', port=5000, debug=False)
