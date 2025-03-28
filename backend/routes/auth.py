# backend/routes/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from backend.utils.data_manager import load_players

auth_bp = Blueprint('auth', __name__)

# Admin Login
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':
            session['is_admin'] = True
            session.pop('player_id', None)
            return redirect(url_for('admin.index'))
        else:
            return render_template('admin_login.html', error="Invalid password")
    return render_template('admin_login.html')


# Admin Logout
@auth_bp.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin.index'))


# Player Login
@auth_bp.route('/player_login', methods=['GET', 'POST'])
def player_login():
    if request.method == 'POST':
        name = request.form['name'].strip().lower()
        access_code = request.form['access_code'].strip()

        players = load_players()
        player = next((p for p in players if p.name.strip().lower() == name and p.access_code == access_code), None)

        if player:
            session['player_id'] = player.id
            session.pop('is_admin', None)
            return redirect(url_for('player_bp.player_page', player_id=player.id))

        return render_template('player_login.html', error='Invalid name or access code.')

    return render_template('player_login.html')

