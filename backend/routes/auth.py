# backend/routes/auth.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from backend.utils.data_manager import load_players

auth_bp = Blueprint('auth', __name__)

# Admin Login
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session.clear()
            session['is_admin'] = True
            session['is_sudo_admin'] = True
            return redirect(url_for('home_bp.index'))
        else:
            return render_template('admin_login.html', error="Invalid password")
    return render_template('admin_login.html')


# Admin Logout
@auth_bp.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('home_bp.index'))


# Player Login
@auth_bp.route('/player_login', methods=['GET', 'POST'])
def player_login():
     players = load_players()
     if request.method == 'POST':
        name = request.form['name'].strip().lower()
        access_code = request.form['access_code'].strip()
        player = next((p for p in players if p.name.strip().lower() == name and p.access_code == access_code), None)

        if player:
            session.clear()
            session['player_id'] = player.id
            session['is_admin'] = False
            return redirect(url_for('player_bp.player_page', player_id=player.id))
        else:
            return render_template('player_login.html', error='Invalid name or access code.')

     return render_template('player_login.html')

#Player logout 

@auth_bp.route('/player_logout')
def player_logout():
    session.clear()
    return redirect(url_for('home_bp.index'))

