import csv
import io

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import bp
from app.auth.forms import CSVUploadForm, ChangePasswordForm, LoginForm
from app.models import batch_create_users, get_user, update_user_password


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
            flash('Logged in successfully.', 'success')
            return redirect(next_page or url_for('quiz.quiz_list'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():
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

        required_fields = {'username', 'email', 'password', 'class', 'academic_year', 'major'}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            flash('CSV must contain columns: username, email, password, class, academic_year, major. '
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
            })

        if not users_list:
            flash('No valid users found in CSV.', 'warning')
        else:
            created, skipped = batch_create_users(users_list)
            results = {'created': created, 'skipped': skipped, 'total': len(users_list)}
            flash(f'Imported {created} users. {len(skipped)} skipped (already exist).', 'success')

    return render_template('admin/import_users.html', form=form, results=results)


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
            logout_user()
            flash('Password updated. Please log in again.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/change_password.html', form=form)
