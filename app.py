from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.secret_key = 'vulnerable_secret_key'  # In production, use a secure random key

# Simple in-memory user database
users_db = {
    'admin': {
        'id': str(uuid.uuid4()),
        'username': 'admin',
        'email': 'admin@example.com',
        'password_hash': generate_password_hash('admin123')
    },
    'user1': {
        'id': str(uuid.uuid4()),
        'username': 'user1',
        'email': 'user1@example.com',
        'password_hash': generate_password_hash('password123')
    }
}

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        username = get_username_by_id(session['user_id'])
        return render_template('dashboard.html', username=username)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users_db:
            user = users_db[username]
            if check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        
        flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """VULNERABLE: Reset password without verifying existing password"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('reset_password.html')
        
        # VULNERABILITY: No verification of existing password!
        # This allows anyone with access to the session to change the password
        username = session['username']
        users_db[username]['password_hash'] = generate_password_hash(new_password)
        
        flash('Password reset successful!', 'success')
        return redirect(url_for('index'))
    
    return render_template('reset_password.html')

def get_username_by_id(user_id):
    """Helper function to get username by user ID"""
    for username, user_data in users_db.items():
        if user_data['id'] == user_id:
            return username
    return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)