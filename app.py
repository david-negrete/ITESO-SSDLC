"""Classroom application with synthetic profiles and server-side authorization."""
import os
import secrets
import time
from datetime import timedelta
from threading import Lock

from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get('APP_SECRET_KEY'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('APP_LOCAL_HTTP') != '1',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=4096,
        ALICE_PASSWORD=os.environ.get('ALICE_PASSWORD'),
        BOB_PASSWORD=os.environ.get('BOB_PASSWORD'),
        ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD'),
    )
    if config:
        app.config.update(config)
    instance_id = secrets.token_hex(12)
    if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY']) < 32:
        raise ValueError('APP_SECRET_KEY must contain at least 32 characters.')
    for key in ('ALICE_PASSWORD', 'BOB_PASSWORD', 'ADMIN_PASSWORD'):
        if not app.config.get(key) or len(app.config[key]) < 16:
            raise ValueError(f'{key} must contain at least 16 characters.')

    profiles = {
        1: {'id': 1, 'username': 'alice', 'name': 'Alice Rivera', 'team': 'Product', 'bio': 'Synthetic classroom profile.'},
        2: {'id': 2, 'username': 'bob', 'name': 'Bob Chen', 'team': 'Support', 'bio': 'Synthetic classroom profile.'},
        3: {'id': 3, 'username': 'admin', 'name': 'Instructor', 'team': 'Teaching', 'bio': 'Synthetic administrator profile.'},
    }
    users = {
        name: {'id': uid, 'role': 'admin' if uid == 3 else 'user',
               'password_hash': generate_password_hash(app.config[f'{name.upper()}_PASSWORD'])}
        for uid, name in ((1, 'alice'), (2, 'bob'), (3, 'admin'))
    }
    dummy_hash = generate_password_hash(secrets.token_urlsafe(24))
    active_sessions, attempts = {}, {}
    lock = Lock()

    def current_user():
        token = session.get('sid')
        with lock:
            record = active_sessions.get(token)
            if not record or record['expires'] <= time.monotonic():
                active_sessions.pop(token, None)
                return None
            return users[record['username']]

    @app.before_request
    def validate_csrf():
        if request.method in ('POST', 'PATCH', 'PUT', 'DELETE'):
            expected = session.get('csrf')
            supplied = request.headers.get('X-CSRF-Token', '')
            if not expected or not secrets.compare_digest(expected, supplied):
                return jsonify(error='Invalid CSRF token.'), 403

    @app.after_request
    def security_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.get('/')
    def home():
        return render_template('index.html')

    @app.get('/health')
    def health():
        return jsonify(status='ok', revision=os.environ.get('RENDER_GIT_COMMIT', 'local'), instance=instance_id)

    @app.get('/api/csrf')
    def csrf():
        session.setdefault('csrf', secrets.token_urlsafe(32))
        return jsonify(token=session['csrf'])

    @app.post('/api/login')
    def login():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error='Expected a JSON object.'), 400
        username, password = payload.get('username', ''), payload.get('password', '')
        if not isinstance(username, str) or not isinstance(password, str):
            return jsonify(error='Invalid credentials.'), 401
        now = time.monotonic()
        key = (request.remote_addr, username[:64])
        with lock:
            if len(attempts) > 1000:
                attempts.clear()
            recent = [t for t in attempts.get(key, []) if now - t < 60]
            if len(recent) >= 5:
                return jsonify(error='Too many attempts. Try again in one minute.'), 429
            attempts[key] = recent + [now]
        user = users.get(username)
        valid = check_password_hash(user['password_hash'] if user else dummy_hash, password)
        if not user or not valid:
            return jsonify(error='Invalid credentials.'), 401
        with lock:
            attempts.pop(key, None)
            active_sessions.pop(session.get('sid'), None)
            for token in list(active_sessions):
                if active_sessions[token]['expires'] <= now:
                    del active_sessions[token]
            if len(active_sessions) >= 1000:
                return jsonify(error='Session capacity reached.'), 503
            token = secrets.token_urlsafe(32)
            active_sessions[token] = {'username': username, 'expires': now + 1800}
        session.clear()
        session.permanent = True
        session['sid'], session['csrf'] = token, secrets.token_urlsafe(32)
        return jsonify(id=user['id'], role=user['role'], username=username)

    @app.post('/api/logout')
    def logout():
        with lock:
            active_sessions.pop(session.get('sid'), None)
        session.clear()
        return jsonify(status='logged out')

    @app.get('/api/me')
    def me():
        user = current_user()
        if not user:
            return jsonify(error='Authentication required.'), 401
        return jsonify(id=user['id'], role=user['role'])

    @app.route('/api/profiles/<int:profile_id>', methods=['GET', 'PATCH'])
    def profile(profile_id):
        user = current_user()
        if not user:
            return jsonify(error='Authentication required.'), 401
        if user['role'] != 'admin' and user['id'] != profile_id:
            return jsonify(error='Access denied.'), 403
        with lock:
            target = profiles.get(profile_id)
            if target is None:
                return jsonify(error='Profile not found.'), 404
            if request.method == 'PATCH':
                payload = request.get_json(silent=True)
                if not isinstance(payload, dict) or not payload or set(payload) - {'bio'}:
                    return jsonify(error='Only bio can be updated.'), 400
                if not isinstance(payload['bio'], str) or len(payload['bio']) > 200:
                    return jsonify(error='Bio must be text with at most 200 characters.'), 400
                target['bio'] = payload['bio']
            return jsonify(dict(target))

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error='Request too large.'), 413

    return app
