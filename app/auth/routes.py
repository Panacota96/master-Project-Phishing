import csv
import io
from urllib.parse import urlparse

from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash

from app.auth import bp
from app.auth.forms import CSVUploadForm, ChangePasswordForm, CohortQRForm, LoginForm, RegistrationForm
from app.auth.sso import handle_sso_callback, initiate_sso_login
from app.models import (
    batch_create_users,
    enqueue_registration,
    get_user,
    get_user_by_email,
    update_user_password,
)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('quiz.quiz_list'))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                parsed_next = urlparse(next_page)
                if (
                    not next_page.startswith('/')
                    or next_page.startswith('//')
                    or parsed_next.scheme
                    or parsed_next.netloc
                ):
                    next_page = None
            flash('Logged in successfully.', 'success')
            return redirect(next_page or url_for('quiz.quiz_list'))
        flash('Invalid username or password.', 'danger')
    sso_enabled = bool(
        current_app.config.get('MSAL_CLIENT_ID')
        and current_app.config.get('MSAL_CLIENT_SECRET')
    )
    return render_template('auth/login.html', form=form, sso_enabled=sso_enabled)


@bp.route('/logout')
def logout():
    session.pop('inspector_email_pool', None)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/admin/import-users', methods=['GET', 'POST'])
@login_required
def import_users():
    if not current_user.is_admin:
        abort(403)

    form = CSVUploadForm()
    results = None

    if form.validate_on_submit():
        stream = io.StringIO(form.csv_file.data.read().decode('utf-8'))
        reader = csv.DictReader(stream)

        required_fields = {'username', 'email', 'password', 'class', 'academic_year', 'major', 'facility'}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            flash('CSV must contain columns: username, email, password, class, academic_year, major, facility. '
                  'Optional: group', 'danger')
            return render_template('admin/import_users.html', form=form, results=results)

        users_list = []
        for row in reader:
            username = row['username'].strip()
            email = row['email'].strip()
            password = row['password'].strip()
            group = row.get('group', 'default').strip() or 'default'
            class_name = row.get('class', 'unknown').strip() or 'unknown'
            academic_year = row.get('academic_year', 'unknown').strip() or 'unknown'
            major = row.get('major', 'unknown').strip() or 'unknown'
            facility = row.get('facility', 'unknown').strip() or 'unknown'

            if not username or not email or not password:
                continue

            users_list.append({
                'username': username,
                'email': email,
                'password': password,
                'group': group,
                'class_name': class_name,
                'academic_year': academic_year,
                'major': major,
                'facility': facility,
            })

        if not users_list:
            flash('No valid users found in CSV.', 'warning')
        else:
            created, skipped = batch_create_users(users_list)
            results = {'created': created, 'skipped': skipped, 'total': len(users_list)}
            flash(f'Imported {created} users. {len(skipped)} skipped (already exist).', 'success')

    return render_template('admin/import_users.html', form=form, results=results)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        errors = False
        if get_user(username):
            form.username.errors.append('Username already taken.')
            errors = True
        if get_user_by_email(email):
            form.email.errors.append('An account with this email already exists.')
            errors = True
        if not errors:
            queue_url = current_app.config.get('SQS_REGISTRATION_QUEUE_URL', '')
            if not queue_url:
                flash('Registration is temporarily unavailable. Please contact your administrator.', 'danger')
                return render_template('auth/register.html', form=form)

            payload = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(form.password.data),
                'class_name': form.class_name.data.strip(),
                'academic_year': form.academic_year.data.strip(),
                'major': form.major.data.strip(),
                'facility': form.facility.data.strip(),
                'group': 'default',
            }
            enqueue_registration(current_app.sqs_client, queue_url, payload)
            return render_template('auth/register_pending.html', email=email)

    return render_template('auth/register.html', form=form)


@bp.route('/admin/generate-qr', methods=['GET', 'POST'])
@login_required
def generate_qr():
    """Generate a generic QR code pointing to the self-registration page."""
    if not current_user.is_admin:
        abort(403)

    import base64
    from io import BytesIO

    import qrcode

    form = CohortQRForm()
    qr_png = None

    if form.validate_on_submit():
        app_base = current_app.config.get('APP_LOGIN_URL', request.host_url.rstrip('/') + '/auth/login')
        register_url = app_base.replace('/auth/login', '') + url_for('auth.register')

        img = qrcode.make(register_url)
        buf = BytesIO()
        img.save(buf, format='PNG')
        qr_png = base64.b64encode(buf.getvalue()).decode()

    return render_template('auth/generate_qr.html', form=form, qr_png=qr_png)


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            update_user_password(current_user.username, form.new_password.data)
            current_user.set_password(form.new_password.data)
            session.pop('inspector_email_pool', None)
            logout_user()
            flash('Password updated. Please log in again.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/change_password.html', form=form)


@bp.route('/sso/login')
def sso_login():
    """Redirect to Microsoft login (MSAL OIDC flow)."""
    return initiate_sso_login()


@bp.route('/sso/callback')
def sso_callback():
    """Handle the redirect back from Microsoft after authentication."""
    return handle_sso_callback()
