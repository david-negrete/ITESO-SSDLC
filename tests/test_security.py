import secrets
import unittest
from unittest.mock import patch

from app import create_app


class ProfileSecurityTests(unittest.TestCase):
    def setUp(self):
        self.passwords = {name: secrets.token_urlsafe(20) for name in ('alice', 'bob', 'admin')}
        config = {'TESTING': True, 'SECRET_KEY': secrets.token_urlsafe(48), 'SESSION_COOKIE_SECURE': False}
        config.update({f'{name.upper()}_PASSWORD': value for name, value in self.passwords.items()})
        self.app = create_app(config)
        self.client = self.app.test_client()

    def send(self, path, method='POST', data=None, csrf=True):
        headers = {'X-CSRF-Token': self.client.get('/api/csrf').json['token']} if csrf else {}
        return self.client.open(path, method=method, json=data, headers=headers)

    def login(self, username='alice'):
        return self.send('/api/login', data={'username': username, 'password': self.passwords[username]})

    def test_TC_AUTH_01_valid_login(self):
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.get('/api/me').json['id'], 1)

    def test_TC_AUTH_02_generic_bad_credentials(self):
        known = self.send('/api/login', data={'username': 'alice', 'password': 'wrong'})
        unknown = self.send('/api/login', data={'username': 'unknown', 'password': 'wrong'})
        self.assertEqual(known.status_code, 401)
        self.assertEqual(known.json, unknown.json)

    def test_TC_AUTH_03_no_unauthenticated_profile(self):
        self.assertEqual(self.client.get('/api/profiles/1').status_code, 401)

    def test_TC_AUTHZ_01_owner_can_read(self):
        self.login()
        response = self.client.get('/api/profiles/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['username'], 'alice')

    def test_TC_AUTHZ_02_other_profile_is_denied(self):
        self.login()
        response = self.client.get('/api/profiles/2')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('bio', response.json)
        self.assertNotIn('name', response.json)

    def test_TC_AUTHZ_03_other_profile_cannot_be_modified(self):
        self.login()
        self.assertEqual(self.send('/api/profiles/2', 'PATCH', {'bio': 'unauthorized'}).status_code, 403)
        self.login('bob')
        self.assertEqual(self.client.get('/api/profiles/2').json['bio'], 'Synthetic classroom profile.')

    def test_TC_AUTHZ_04_owner_can_update(self):
        self.login()
        self.assertEqual(self.send('/api/profiles/1', 'PATCH', {'bio': 'Updated'}).status_code, 200)
        self.assertEqual(self.client.get('/api/profiles/1').json['bio'], 'Updated')

    def test_TC_AUTHZ_05_admin_can_read_other_profiles(self):
        self.login('admin')
        self.assertEqual(self.client.get('/api/profiles/2').status_code, 200)

    def test_TC_AUTHZ_06_role_mass_assignment_is_rejected(self):
        self.login()
        self.assertEqual(self.send('/api/profiles/1', 'PATCH', {'bio': 'x', 'role': 'admin'}).status_code, 400)
        self.assertEqual(self.client.get('/api/profiles/2').status_code, 403)

    def test_TC_CSRF_01_login_requires_csrf(self):
        self.assertEqual(self.send('/api/login', data={'username': 'alice', 'password': self.passwords['alice']}, csrf=False).status_code, 403)

    def test_TC_CSRF_02_update_requires_csrf(self):
        self.login()
        self.assertEqual(self.send('/api/profiles/1', 'PATCH', {'bio': 'x'}, csrf=False).status_code, 403)

    def test_TC_SESS_01_logout_revokes_copied_cookie(self):
        self.login()
        cookie = self.client.get_cookie('session').value
        self.send('/api/logout', data={})
        self.client.set_cookie('session', cookie)
        self.assertEqual(self.client.get('/api/profiles/1').status_code, 401)

    def test_TC_SESS_02_login_rotates_session(self):
        self.login()
        old = self.client.get_cookie('session').value
        self.login()
        self.assertNotEqual(old, self.client.get_cookie('session').value)
        replay = self.app.test_client()
        replay.set_cookie('session', old)
        self.assertEqual(replay.get('/api/profiles/1').status_code, 401)

    def test_TC_SESS_03_absolute_session_expiration(self):
        self.login()
        with patch('app.time.monotonic', return_value=10**12):
            self.assertEqual(self.client.get('/api/profiles/1').status_code, 401)

    def test_TC_INPUT_01_bio_limit_and_type(self):
        self.login()
        for bio in ('x' * 201, 42, None):
            with self.subTest(bio_type=type(bio).__name__):
                self.assertEqual(self.send('/api/profiles/1', 'PATCH', {'bio': bio}).status_code, 400)

    def test_TC_INPUT_02_invalid_json_shape(self):
        self.assertEqual(self.send('/api/login', data=[]).status_code, 400)
        self.login()
        self.assertEqual(self.send('/api/profiles/1', 'PATCH', []).status_code, 400)

    def test_TC_HEADERS_01_security_headers(self):
        response = self.client.get('/')
        self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_TC_SESS_04_production_cookie_attributes(self):
        self.app.config['SESSION_COOKIE_SECURE'] = True
        response = self.client.get('/api/csrf')
        cookie = response.headers['Set-Cookie']
        for attribute in ('Secure', 'HttpOnly', 'SameSite=Lax'):
            self.assertIn(attribute, cookie)
        self.assertIn('Strict-Transport-Security', response.headers)

    def test_TC_AUTH_04_guessing_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.send('/api/login', data={'username': 'alice', 'password': 'wrong'}).status_code, 401)
        self.assertEqual(self.send('/api/login', data={'username': 'alice', 'password': 'wrong'}).status_code, 429)


if __name__ == '__main__':
    unittest.main()
