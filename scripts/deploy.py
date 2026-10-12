"""Request an exact-commit Render deployment, then verify its health revision."""
import json
import os
import time
import urllib.parse
import urllib.request

hook = os.environ['RENDER_DEPLOY_HOOK']
base = os.environ['APP_URL'].rstrip('/')
revision = os.environ['GITHUB_SHA']
if urllib.parse.urlparse(hook).scheme != 'https' or not hook.startswith('https://api.render.com/deploy/'):
    raise SystemExit('Expected an HTTPS Render deploy hook.')
if not base.startswith('https://'):
    raise SystemExit('APP_URL must use HTTPS.')
separator = '&' if '?' in hook else '?'
try:
    with urllib.request.urlopen(hook + separator + urllib.parse.urlencode({'ref': revision}), timeout=30) as response:
        if response.status not in (200, 202):
            raise SystemExit('Deploy request failed.')
except Exception:
    raise SystemExit('Render deploy request failed. Check the configured hook; its value is not logged.') from None
for _ in range(90):
    try:
        with urllib.request.urlopen(base + '/health', timeout=15) as response:
            data = json.load(response)
        if data.get('status') == 'ok' and data.get('revision') == revision:
            print('Deployment verified: running revision matches the tested commit.')
            break
    except (OSError, ValueError):
        pass
    time.sleep(10)
else:
    raise SystemExit('Deployment did not reach the tested revision within 15 minutes.')
