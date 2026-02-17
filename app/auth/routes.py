import csv
import io

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import bp
from app.auth.forms import CSVUploadForm, LoginForm
from app.models import batch_create_users, get_user


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

        required_fields = {'username', 'email', 'password'}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            flash('CSV must contain columns: username, email, password. '
                  'Optional: group', 'danger')
            return render_template('admin/import_users.html', form=form, results=results)

        users_list = []
        for row in reader:
            username = row['username'].strip()
            email = row['email'].strip()
            password = row['password'].strip()
            group = row.get('group', 'default').strip() or 'default'

            if not username or not email or not password:
                continue

            users_list.append({
                'username': username,
                'email': email,
                'password': password,
                'group': group,
            })

        if not users_list:
            flash('No valid users found in CSV.', 'warning')
        else:
            created, skipped = batch_create_users(users_list)
            results = {'created': created, 'skipped': skipped, 'total': len(users_list)}
            flash(f'Imported {created} users. {len(skipped)} skipped (already exist).', 'success')

    return render_template('admin/import_users.html', form=form, results=results)
