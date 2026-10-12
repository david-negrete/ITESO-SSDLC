"""Generate disposable local credentials, then start the loopback-only demo."""
import os
import secrets

from app import create_app

if __name__ == '__main__':
    os.environ['APP_LOCAL_HTTP'] = '1'
    os.environ['APP_SECRET_KEY'] = secrets.token_urlsafe(48)
    for name in ('alice', 'bob', 'admin'):
        password = secrets.token_urlsafe(18)
        os.environ[f'{name.upper()}_PASSWORD'] = password
        print(f'{name}: {password}')
    print('Local demo: http://127.0.0.1:5000 (credentials reset on restart)')
    create_app().run(host='127.0.0.1', port=5000, debug=False)
