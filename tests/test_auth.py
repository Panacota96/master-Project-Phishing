"""Tests for authentication routes."""

from conftest import login


class TestLogin:
    def test_login_page_renders(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'Login' in resp.data

    def test_login_success(self, client, seed_admin):
        resp = login(client, 'admin', 'admin123')
        assert resp.status_code == 200
        assert b'Logged in successfully' in resp.data

    def test_login_wrong_password(self, client, seed_admin):
        resp = login(client, 'admin', 'wrongpass')
        assert b'Invalid username or password' in resp.data

    def test_login_nonexistent_user(self, client):
        resp = login(client, 'ghost', 'pass')
        assert b'Invalid username or password' in resp.data

    def test_logout(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/auth/logout', follow_redirects=True)
        assert b'You have been logged out' in resp.data

    def test_register_route_exists(self, client):
        resp = client.get('/auth/register')
        assert resp.status_code == 200
        assert b'Create Your Account' in resp.data

    def test_login_redirects_authenticated(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/auth/login')
        assert resp.status_code == 302


class TestCSVImport:
    def test_import_requires_admin(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.get('/auth/admin/import-users')
        assert resp.status_code == 403

    def test_import_page_renders_for_admin(self, client, seed_admin):
        login(client, 'admin', 'admin123')
        resp = client.get('/auth/admin/import-users')
        assert resp.status_code == 200
        assert b'Import Users' in resp.data

    def test_import_csv(self, client, app, seed_admin):
        login(client, 'admin', 'admin123')

        csv_content = b'username,email,password,class,academic_year,major,facility,group\njdoe,jdoe@test.com,pass123,Class A,2025,CS,Paris,sales\nasmith,asmith@test.com,pass456,Class A,2025,CS,Paris,sales'
        from io import BytesIO
        data = {
            'csv_file': (BytesIO(csv_content), 'users.csv'),
        }
        resp = client.post('/auth/admin/import-users', data=data,
                           content_type='multipart/form-data', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Imported 2 users' in resp.data

        # Verify users exist
        with app.app_context():
            from app.models import get_user
            assert get_user('jdoe') is not None
            assert get_user('asmith') is not None

    def test_import_csv_skips_existing(self, client, app, seed_admin):
        login(client, 'admin', 'admin123')

        csv_content = b'username,email,password,class,academic_year,major,facility,group\nadmin,other@test.com,pass,Class A,2025,CS,Paris,x\nnewuser,new@test.com,pass,Class A,2025,CS,Paris,x'
        from io import BytesIO
        data = {
            'csv_file': (BytesIO(csv_content), 'users.csv'),
        }
        resp = client.post('/auth/admin/import-users', data=data,
                           content_type='multipart/form-data', follow_redirects=True)
        assert b'1 skipped' in resp.data

    def test_import_csv_missing_columns(self, client, seed_admin):
        login(client, 'admin', 'admin123')

        csv_content = b'name,mail\njdoe,jdoe@test.com'
        from io import BytesIO
        data = {
            'csv_file': (BytesIO(csv_content), 'users.csv'),
        }
        resp = client.post('/auth/admin/import-users', data=data,
                           content_type='multipart/form-data', follow_redirects=True)
        assert b'CSV must contain columns' in resp.data


class TestChangePassword:
    def test_change_password_requires_login(self, client):
        resp = client.get('/auth/change-password')
        assert resp.status_code in (302, 401)

    def test_change_password_wrong_current(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post(
            '/auth/change-password',
            data={
                'current_password': 'wrong',
                'new_password': 'Newpass1!',
                'confirm_password': 'Newpass1!',
            },
            follow_redirects=True,
        )
        assert b'Current password is incorrect' in resp.data

    def test_change_password_strength_validation(self, client, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post(
            '/auth/change-password',
            data={
                'current_password': 'password123',
                'new_password': 'weak',
                'confirm_password': 'weak',
            },
            follow_redirects=True,
        )
        assert b'Password must be at least 8 characters' in resp.data

    def test_change_password_logs_out_and_updates(self, client, app, seed_user):
        login(client, 'testuser', 'password123')
        resp = client.post(
            '/auth/change-password',
            data={
                'current_password': 'password123',
                'new_password': 'Newpass1!',
                'confirm_password': 'Newpass1!',
            },
            follow_redirects=True,
        )
        assert b'Password updated. Please log in again.' in resp.data
        assert b'Login' in resp.data

        with app.app_context():
            from app.models import get_user
            user = get_user('testuser')
            assert user is not None
            assert user.check_password('Newpass1!') is True
            assert user.check_password('password123') is False

        resp = login(client, 'testuser', 'password123')
        assert b'Invalid username or password' in resp.data

        resp = login(client, 'testuser', 'Newpass1!')
        assert b'Logged in successfully' in resp.data
