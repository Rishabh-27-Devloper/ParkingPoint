from flask import Flask, render_template, request, redirect, url_for, flash, session,send_from_directory,jsonify
from functools import wraps
from Database import Database
import smtplib
from email.message import EmailMessage
import random
from werkzeug.security import generate_password_hash
import json, razorpay
from datetime import datetime, timedelta
import uuid,time
import qrcode,os
from io import BytesIO
app = Flask(__name__,static_folder='static', template_folder='templates')
app.secret_key = '#$secret#$NotmuchNeeded$$'

SMTP_SERVER = "XXXX"
SMTP_PORT = "587"
SMTP_USER = "XXXX"
SMTP_PASSWORD = "VVVV"

RAZORPAY_KEY_ID_TEST = "VVVV"
RAZORPAY_KEY_SECRET_TEST = "XXXX"

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID_TEST, RAZORPAY_KEY_SECRET_TEST))

@app.route('/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    file_path = os.path.join(static_dir, filename)
    if os.path.isfile(file_path):
        return send_from_directory(static_dir, filename)
    return '', 404

@app.route('/')
@app.route('/index')
def home():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    return render_template('index.html')
ADMIN_PASSWORD = "admin@123"  # Change this to a strong password in production

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid admin password."
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    db = Database()
    # Fetch admin info (dummy for now)
    admin = {
        "name": "Admin",
        "email": "admin@email.com"
    }
    stats = {
        "total_bookings": 0,
        "total_spots": 0,
        "total_users": 0,
        "revenue": "0.00"
    }
    charts = {
        "bookings": {"labels": [], "data": []},
        "revenue": {"labels": [], "data": []}
    }
    recent_spots = []
    with db._connect() as conn:
        cursor = conn.cursor()
        # Total bookings
        cursor.execute('SELECT COUNT(*) FROM tickets')
        stats["total_bookings"] = cursor.fetchone()[0]
        # Total spots
        cursor.execute('SELECT COUNT(*) FROM parkingspots')
        stats["total_spots"] = cursor.fetchone()[0]
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        stats["total_users"] = cursor.fetchone()[0]
        # Revenue
        cursor.execute('SELECT SUM(amount) FROM payments')
        revenue = cursor.fetchone()[0]
        stats["revenue"] = f"{revenue:.2f}" if revenue else "0.00"
        # Bookings chart (last 7 days)
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', epoch), COUNT(*) 
            FROM tickets 
            WHERE epoch >= date('now', '-6 days')
            GROUP BY strftime('%Y-%m-%d', epoch)
            ORDER BY strftime('%Y-%m-%d', epoch)
        """)
        rows = cursor.fetchall()
        charts["bookings"]["labels"] = [r[0] for r in rows]
        charts["bookings"]["data"] = [r[1] for r in rows]
        # Revenue chart (last 7 days)
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', timestamp), SUM(amount) 
            FROM payments 
            WHERE timestamp >= date('now', '-6 days')
            GROUP BY strftime('%Y-%m-%d', timestamp)
            ORDER BY strftime('%Y-%m-%d', timestamp)
        """)
        rows = cursor.fetchall()
        charts["revenue"]["labels"] = [r[0] for r in rows]
        charts["revenue"]["data"] = [float(r[1]) for r in rows]
        # Recent parking spots
        cursor.execute("""
            SELECT name, locality, capacity, rate, status 
            FROM parkingspots
        """)
        recent_spots = [
            {
                "name": r[0],
                "location": r[1],
                "capacity": r[2],
                "rate": r[3],
                "status": r[4]
            }
            for r in cursor.fetchall()
        ]
    return render_template(
        'admin.html',
        admin=admin,
        stats=stats,
        charts=charts,
        recent_spots=recent_spots
    )

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/spots/register', methods=['POST'])
@admin_login_required
def register_parking_spot():
    if request.method == 'POST':
        name = request.form.get('spot_name', '').strip()
        locality = request.form.get('location', '').strip()
        capacity = request.form.get('capacity', '').strip()
        rate = request.form.get('rate', '').strip()
        status = request.form.get('status', 'Available')
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        coordinates = json.dumps([latitude,longitude])
        if not name or not locality or not capacity or not rate:
            error = "All fields are required."
            flash(error, "danger")
            return redirect(url_for('admin_dashboard'))
        else:
            db = Database()
            with db._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO parkingspots (name, locality, capacity, rate, status,coordinates) VALUES (?, ?, ?, ?, ?, ?)',
                    (name, locality, int(capacity), float(rate), status,coordinates)
                )
                conn.commit()
                flash("Parking spot registered successfully!", "success")
                return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not email or not password:
            error = "Please enter both email and password."
        else:
            db = Database()
            with db._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, password FROM users WHERE email=?', (email,))
                user = cursor.fetchone()
                if user and user[2] == password:
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    return redirect(url_for('profile'))
                else:
                    error = "Invalid email or password."
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    error = None
    if request.method == 'POST':
        username = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')

        if not username or not email or not password or not confirm_password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif not terms:
            error = "You must agree to the Terms of Service."
        else:
            db = Database()
            with db._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM users WHERE username=? OR email=?', (username, email))
                if cursor.fetchone():
                    error = "Username or email already exists."
                else:
                    otp = generate_otp()
                    status, _ = send_Email_with_OTP(email, otp)
                    if status:
                        session['pending_signup'] = {
                            'username': username,
                            'email': email,
                            'password': password,
                            'otp': otp
                        }
                        return render_template('verify.html', email=email)
                    else:
                        error = "Failed to send verification email. Please try again later."
    return render_template('signup.html', error=error)

@app.route('/verify-email', methods=['POST'])
def verify_email():
    error = None
    message = None
    pending = session.get('pending_signup')
    if not pending:
        error = "Session expired. Please sign up again."
        return redirect(url_for('signup'))
    email = pending['email']
    # Collect OTP from form
    otp_input = ''.join([request.form.get(f'otp{i}', '') for i in range(6)])
    if not otp_input or len(otp_input) != 6 or not otp_input.isdigit():
        error = "Please enter the 6-digit OTP."
        return render_template('verify.html', email=email, error=error)
    if otp_input == pending.get('otp'):
        # Register user
        db = Database()
        success = db.signup_user(pending['username'], pending['password'], pending['email'])
        if success:
            session.pop('pending_signup', None)
            flash('Signup successful! Please log in.')
            return redirect(url_for('login'))
        else:
            error = "Username or email already exists."
            session.pop('pending_signup', None)
            return render_template('signup.html', error=error)
    else:
        error = "Invalid OTP. Please try again."
        return render_template('verify.html', email=email, error=error)

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    pending = session.get('pending_signup')
    if not pending:
        flash("Session expired. Please sign up again.", "danger")
        return redirect(url_for('signup'))
    email = pending['email']
    otp = generate_otp()
    status, _ = send_Email_with_OTP(email, otp)
    if status:
        session['pending_signup']['otp'] = otp
        message = "A new OTP has been sent to your email."
        return render_template('verify.html', email=email, message=message)
    else:
        error = "Failed to resend OTP. Please try again later."
        return render_template('verify.html', email=email, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access your dashboard.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(404)
def not_found(e):
    return render_template('notfound.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error=str(e)), 500

@app.route('/profile')
@login_required
def profile():
    db = Database()
    user_id = session.get('user_id')
    with db._connect() as conn:
        cursor = conn.cursor()
        # Fetch user info
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='default_avatar.png')
        }
        # Fetch stats
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE owner_email=? AND entry=0', (row[1],))
        active_bookings = cursor.fetchone()[0] if cursor.rowcount else 0
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE user_id=?', (user_id,))
        vehicles = cursor.fetchone()[0] if cursor.rowcount else 0
        # cursor.execute('SELECT wallet_balance FROM users WHERE id=?', (user_id,))
        # wallet_balance_row = cursor.fetchone()
        # wallet_balance = f"{wallet_balance_row[0]:.2f}" if wallet_balance_row and wallet_balance_row[0] is not None else "0.00"
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id=? AND seen=0', (user_id,))
        notifications = cursor.fetchone()[0] if cursor.rowcount else 0
        stats = {
            "active_bookings": active_bookings,
            "vehicles": vehicles,
            "wallet_balance": "0.00",
            "notifications": notifications
        }
        # Fetch recent bookings (limit 5)
        cursor.execute("""
            SELECT t.id, p.name, t.entry_epoch, v.number, t.entry, t.amount
            FROM tickets t
            LEFT JOIN parkingspots p ON t.spot_id = p.id
            LEFT JOIN vehicles v ON t.vehicle_id = v.id
            WHERE t.owner_email=?
            ORDER BY t.epoch DESC
            LIMIT 5
        """, (row[1],))
        recent_bookings = []
        for r in cursor.fetchall():
            # Status mapping: 0 = Active, 1 = Completed, 2 = Cancelled
            status_map = {0: 'Active', 1: 'Completed', 2: 'Cancelled'}
            status = status_map.get(r[4], 'Unknown')
            # Convert entry_epoch (assumed as UNIX timestamp) to readable date string
            date_str = datetime.fromtimestamp(r[2]).strftime('%Y-%m-%d %H:%M:%S') if r[2] else "N/A"
            recent_bookings.append({
                "lot_name": r[1] or "N/A",
                "date": date_str,
                "vehicle": r[3] or "N/A",
                "status": status,
                "amount": str(r[5]) if r[5] is not None else "0"
            })
    return render_template(
        'profile.html',
        user=user,
        stats=stats,
        recent_bookings=recent_bookings
    )

@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    db = Database()
    user_id = session.get('user_id')
    user = {}
    parking_lots = []
    vehicles = []

    with db._connect() as conn:
        cursor = conn.cursor()
        # User info for sidebar/header
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='avator.jpg')
        }
        # Parking lots with available spots
        cursor.execute('SELECT id, name, locality, capacity, rate FROM parkingspots WHERE status="Available"')
        lots = cursor.fetchall()
        for lot in lots:
            # Count available spots (for demo, assume all spots are available)
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE spot_id=? AND entry=0', (lot[0],))
            booked = cursor.fetchone()[0]
            available_spots = max(0, lot[3] - booked)
            parking_lots.append({
                "id": lot[0],
                "name": lot[1],
                "locality": lot[2],
                "capacity": lot[3],
                "rate": lot[4],
                "available_spots": available_spots
            })
        # User vehicles
        cursor.execute('SELECT id, type, model, number FROM vehicles WHERE user_id=?', (user_id,))
        vehicles = [
            {
                "id": v[0],
                "type": v[1],
                "model": v[2],
                "number": v[3]
            }
            for v in cursor.fetchall()
        ]
    return render_template('newBook.html', user=user, parking_lots=parking_lots, vehicles=vehicles)

@app.route('/payments')
@login_required
def payments():
    db = Database()
    user_id = session.get('user_id')
    with db._connect() as conn:
        cursor = conn.cursor()
        # Fetch user info for sidebar/header
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='avator.jpg')
        }
        # Fetch all payments for this user (no filter on status)
        cursor.execute("""
            SELECT pay.transaction_id, pay.timestamp, p.name, v.number, pay.amount, pay.status, pay.method
            FROM payments pay
            LEFT JOIN tickets t ON pay.ticket_id = t.id
            LEFT JOIN parkingspots p ON t.spot_id = p.id
            LEFT JOIN vehicles v ON t.vehicle_id = v.id
            WHERE pay.user_id=?
            ORDER BY pay.timestamp DESC
        """, (user_id,))
        payments = []
        results = cursor.fetchall()
        for r in results:
            status_map = {
                'SUCCESS': 'Success',
                'FAILED': 'Failed',
                'PENDING': 'Pending'
            }
            status = status_map.get(str(r[5]).upper(), str(r[5]).capitalize() if r[5] else "Unknown")
            payments.append({
                "id": r[0],
                "date": r[1],
                "lot_name": r[2] or "N/A",
                "vehicle": r[3] or "N/A",
                "amount": str(r[4]) if r[4] is not None else "0",
                "status": status,
                "method": r[6] or "N/A"
            })
    return render_template('payments.html', user=user, payments=payments)

@app.route('/my-bookings')
@login_required
def my_bookings():
    db = Database()
    user_id = session.get('user_id')
    with db._connect() as conn:
        cursor = conn.cursor()
        # Fetch user info for sidebar/header
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='avator.jpg')
        }
        # Fetch all bookings for this user
        cursor.execute("""
            SELECT t.id, p.name, t.epoch, v.number, t.exit, t.amount
            FROM tickets t
            LEFT JOIN parkingspots p ON t.spot_id = p.id
            LEFT JOIN vehicles v ON t.vehicle_id = v.id
            WHERE t.owner_email=?
            ORDER BY t.epoch DESC
        """, (row[1],))
        bookings = []
        results = cursor.fetchall()
        print(results)
        for r in results:
            # Status mapping: 0 = Active, 1 = Completed, 2 = Cancelled
            status_map = {0: 'Active', 1: 'Completed', 2: 'Cancelled'}
            status = status_map.get(r[4], 'Unknown')
            # Convert epoch (assumed as UNIX timestamp) to readable date string
            date_str = datetime.fromtimestamp(r[2]).strftime('%Y-%m-%d %H:%M:%S') if r[2] else "N/A"
            bookings.append({
                "id": r[0],
                "lot_name": r[1] or "N/A",
                "date": date_str,
                "vehicle": r[3] or "N/A",
                "status": status,
                "amount": str(r[5]) if r[5] is not None else "0"
            })
    return render_template('bookings.html', user=user, bookings=bookings)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/notifications')
@login_required
def notifications():
    db = Database()
    user_id = session.get('user_id')
    with db._connect() as conn:
        cursor = conn.cursor()
        # Fetch user info for sidebar/header
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='default_avatar.png')
        }
        # Fetch notifications for this user
        cursor.execute('SELECT id, message, timestamp, seen FROM notifications WHERE user_id=? ORDER BY timestamp DESC', (user_id,))
        notifications = [
            {
                "id": n[0],
                "message": n[1],
                "created_at": n[2],
                "seen": bool(n[3])
            }
            for n in cursor.fetchall()
        ]
    return render_template('notifications.html', user=user, notifications=notifications)

@app.route('/support')
@login_required
def support():
    db = Database()
    user_id = session.get('user_id')
    # Fetch user info for sidebar/header
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='default_avatar.png')
        }
    return render_template('support.html', user=user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db = Database()
    user_id = session.get('user_id')
    error = None
    message = None
    user = {}

    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, email, email_notifications, sms_notifications, language, private_profile FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else "",
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='avator.jpg'),
            "email_notifications": bool(row[2]) if row else False,
            "sms_notifications": bool(row[3]) if row else False,
            "language": row[4] if row else "en",
            "private_profile": bool(row[5]) if row else False
        }

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            email_notifications = 1 if request.form.get('email_notifications') else 0
            sms_notifications = 1 if request.form.get('sms_notifications') else 0
            language = request.form.get('language', 'en')
            private_profile = 1 if request.form.get('private_profile') else 0

            # Handle password change
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            if password or confirm_password:
                if password != confirm_password:
                    error = "Passwords do not match."
                elif len(password) < 6:
                    error = "Password must be at least 6 characters."
                else:
                    hashed_pw = generate_password_hash(password)
                    cursor.execute('UPDATE users SET password=? WHERE id=?', (hashed_pw, user_id))
                    conn.commit()
                    message = "Password updated successfully."

            if not error:
                cursor.execute('''
                    UPDATE users SET username=?, email=?, email_notifications=?, sms_notifications=?, language=?, private_profile=?
                    WHERE id=?
                ''', (
                    name, email, email_notifications, sms_notifications, language, private_profile, user_id
                ))
                conn.commit()
                message = message or "Settings updated successfully."
            # Update user dict for rendering
            user.update({
                "name": name,
                "email": email,
                "avatar_url": url_for('static', filename='avator.jpg'),
                "email_notifications": bool(email_notifications),
                "sms_notifications": bool(sms_notifications),
                "language": language,
                "private_profile": bool(private_profile)
            })

        return render_template('settings.html', user=user, error=error, message=message)

@app.route('/vehicles')
@login_required
def vehicles():
    db = Database()
    user_id = session.get('user_id')
    # Fetch user info for sidebar/header
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='default_avatar.png')
        }
        # Fetch vehicles for this user
        cursor.execute('SELECT id, type, model, number, color FROM vehicles WHERE user_id=?', (user_id,))
        vehicles = [
            {
                "id": v[0],
                "type": v[1],
                "model": v[2],
                "number": v[3],
                "color": v[4]
            }
            for v in cursor.fetchall()
        ]
        # Stats for widgets
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE owner_email=? AND entry=0', (user_id,))
        active_bookings = cursor.fetchone()[0] if cursor.rowcount else 0
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE user_id=?', (user_id,))
        vehicle_count = cursor.fetchone()[0] if cursor.rowcount else 0
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id=? AND seen=0', (user_id,))
        notifications = cursor.fetchone()[0] if cursor.rowcount else 0
        stats = {
            "active_bookings": active_bookings,
            "vehicles": vehicle_count,
            "notifications": notifications
        }
    return render_template('vehicles.html', user=user, vehicles=vehicles, stats=stats)

@app.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    db = Database()
    user_id = session.get('user_id')
    error = None
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
    user = {
        "name": session.get('username', 'User'),
        "email": row[1] if row else "",
        "avatar_url": url_for('static', filename='avator.jpg')
    }
    if request.method == 'POST':
        vtype = request.form.get('type', '').strip()
        model = request.form.get('model', '').strip()
        number = request.form.get('number', '').strip().upper()
        color = request.form.get('color', '').strip()
        if not vtype or not model or not number or not color:
            error = "All fields are required."
        else:
            with db._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM vehicles WHERE user_id=? AND number=?', (user_id, number))
                if cursor.fetchone():
                    error = "Vehicle with this number already exists."
                else:
                    cursor.execute(
                        'INSERT INTO vehicles (user_id, type, model, number, color) VALUES (?, ?, ?, ?, ?)',
                        (user_id, vtype, model, number, color)
                    )
                    conn.commit()
                    return redirect(url_for('vehicles'))
    return render_template('add-vehicle.html', error=error, user=user)

@app.route('/vehicles/edit/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    db = Database()
    user_id = session.get('user_id')
    error = None
    user = None
    vehicle_data = None

    with db._connect() as conn:
        cursor = conn.cursor()
        # Fetch user info for sidebar/header
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='avator.jpg')
        }
        # Fetch vehicle info
        cursor.execute('SELECT id, type, model, number, color FROM vehicles WHERE id=? AND user_id=?', (vehicle_id, user_id))
        vehicle = cursor.fetchone()
        if not vehicle:
            flash("Vehicle not found.", "danger")
            return redirect(url_for('vehicles'))

        if request.method == 'POST':
            vtype = request.form.get('type', '').strip()
            model = request.form.get('model', '').strip()
            number = request.form.get('number', '').strip().upper()
            color = request.form.get('color', '').strip()
            if not vtype or not model or not number or not color:
                error = "All fields are required."
            else:
                # Check for duplicate number (except self)
                cursor.execute('SELECT id FROM vehicles WHERE user_id=? AND number=? AND id!=?', (user_id, number, vehicle_id))
                if cursor.fetchone():
                    error = "Another vehicle with this number already exists."
                else:
                    cursor.execute(
                        'UPDATE vehicles SET type=?, model=?, number=?, color=? WHERE id=? AND user_id=?',
                        (vtype, model, number, color, vehicle_id, user_id)
                    )
                    conn.commit()
                    return redirect(url_for('vehicles'))
            # If error, keep form data
            vehicle_data = {
                "id": vehicle_id,
                "type": vtype,
                "model": model,
                "number": number,
                "color": color
            }
        else:
            # GET: show current vehicle data
            vehicle_data = {
                "id": vehicle[0],
                "type": vehicle[1],
                "model": vehicle[2],
                "number": vehicle[3],
                "color": vehicle[4]
            }

    return render_template('edit_vehicle.html', vehicle=vehicle_data, error=error, user=user)

@app.route('/vehicles/delete/<int:vehicle_id>')
@login_required
def delete_vehicle(vehicle_id):
    db = Database()
    user_id = session.get('user_id')
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vehicles WHERE id=? AND user_id=?', (vehicle_id, user_id))
        conn.commit()
    flash("Vehicle deleted successfully.", "success")
    return redirect(url_for('vehicles'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash("Please enter your email address.", "danger")
            return render_template('forgot_password.html')
        db = Database()
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email=?', (email,))
            user = cursor.fetchone()
            if not user:
                flash("No account found with that email.", "danger")
                return render_template('forgot_password.html')
            otp = generate_otp()
            status, _ = send_Email_with_OTP(email, otp)
            if status:
                session['reset_password'] = {'email': email, 'otp': otp}
                flash("An OTP has been sent to your email. Please enter it below to reset your password.", "success")
                return redirect(url_for('reset_password_otp'))
            else:
                flash("Failed to send OTP. Please try again later.", "danger")
                return render_template('forgot_password.html')
    return render_template('forgot_password.html')

@app.route('/reset-password-otp', methods=['GET', 'POST'])
def reset_password_otp():
    pending = session.get('reset_password')
    if not pending:
        flash("Session expired. Please try again.", "danger")
        return redirect(url_for('forgot_password'))
    email = pending['email']
    if request.method == 'POST':
        otp_input = ''.join([request.form.get(f'otp{i}', '') for i in range(6)])
        if not otp_input or len(otp_input) != 6 or not otp_input.isdigit():
            flash("Please enter the 6-digit OTP.", "danger")
            return render_template('reset_password_otp.html', email=email)
        if otp_input == pending.get('otp'):
            session['reset_password_verified'] = email
            session.pop('reset_password', None)
            return redirect(url_for('reset_password_new'))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return render_template('reset_password_otp.html', email=email)
    return render_template('reset_password_otp.html', email=email)

@app.route('/reset-password-new', methods=['GET', 'POST'])
def reset_password_new():
    email = session.get('reset_password_verified')
    if not email:
        flash("Session expired. Please try again.", "danger")
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not password or not confirm_password:
            flash("Please fill out all fields.", "danger")
            return render_template('reset_password_new.html')
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password_new.html')
        db = Database()
        with db._connect() as conn:
            cursor = conn.cursor()
            # Optionally hash the password here
            cursor.execute('UPDATE users SET password=? WHERE email=?', (password, email))
            conn.commit()
        session.pop('reset_password_verified', None)
        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('reset_password_new.html')

@app.route('/otp')
def otp():
    status,otp = send_Email_with_OTP('r0207shukla@gmail.com')
    if status:
        return f"OTP sent successfully: {otp}"
    else:
        return "Failed to send OTP. Please try again later."

def generate_otp(length=6):
    return ''.join(random.choices('0123456789', k=length))

def send_Email_with_OTP(to_email,otp=None):
    if not otp: otp = generate_otp()
    subject = f"Parking Point: Email Verification OTP - {otp}"
    body = f"""
    <html>
    <head>
      <style>
        body {{
          background: #f7f9fb;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          color: #2c5aa0;
          margin: 0;
          padding: 0;
        }}
        .email-container {{
          max-width: 480px;
          margin: 40px auto;
          background: #fff;
          border-radius: 18px;
          box-shadow: 0 8px 32px rgba(44,90,160,0.08);
          padding: 2.5rem 2rem 2rem 2rem;
          text-align: center;
        }}
        .logo-img {{
          width: 60px;
          height: 60px;
          border-radius: 10px;
          margin-bottom: 1.2rem;
        }}
        .otp-title {{
          font-size: 1.5rem;
          font-weight: 700;
          margin-bottom: 0.7rem;
          color: #2c5aa0;
        }}
        .otp-code {{
          display: inline-block;
          background: #f0f4fa;
          color: #ff6b6b;
          font-size: 2.2rem;
          font-weight: bold;
          letter-spacing: 0.3rem;
          padding: 0.7rem 2.2rem;
          border-radius: 12px;
          margin: 1.2rem 0;
          box-shadow: 0 2px 12px rgba(44,90,160,0.10);
        }}
        .otp-desc {{
          color: #444;
          font-size: 1.08rem;
          margin-bottom: 1.5rem;
        }}
        .footer {{
          margin-top: 2.5rem;
          color: #888;
          font-size: 0.98rem;
        }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <img src="https://i.ibb.co/fVMGV7WV/Logo.jpg" alt="Parking Point" class="logo-img" />
        <div class="otp-title">Verify Your Email Address</div>
        <div class="otp-desc">
          Please use the following OTP to complete your registration with <b>Parking Point</b>:
        </div>
        <div class="otp-code">{otp}</div>
        <div class="otp-desc">
          This OTP is valid for a limited time. Do not share it with anyone.<br>
          If you did not request this, you can safely ignore this email.
        </div>
        <div class="footer">
          Thank you for choosing Parking Point!<br>
          <span style="color:#2c5aa0;">parkingpoint.co</span>
        </div>
      </div>
    </body>
    </html>
    """
    try:
        print(f"Sending email to {to_email} with subject '{subject}' (HTML body)")
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = "Rishabh27@outlook.in"
        msg['To'] = to_email
        msg.set_content("Your email client does not support HTML emails. Your OTP is: " + otp)
        msg.add_alternative(body, subtype='html')
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp: # type: ignore
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
            return [True,otp]
    except Exception as e:
        print(f"Failed to send email: {e}")
        return [False,otp]

def get_current_user_details():
    db = Database()
    user_id = session.get('user_id')
    if not user_id:
        return None
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "name": row[0],
                "email": row[1],
                "avatar_url": url_for('static', filename='avator.jpg')
            }
    return None

@app.route('/create_order', methods=['POST'])
@login_required
def create_order():
    # Accept form data (not JSON) for amount
    amount = request.form.get('amount')
    booking_details = request.form.get('booking')
    if not amount or not amount.isdigit():
        flash("Invalid amount.", "danger")
        return redirect(url_for('payments'))
    amount_int = int(amount)
    if amount_int <= 0:
        flash("Amount must be greater than zero.", "danger")
        return redirect(url_for('payments'))
    # Razorpay expects amount in paise
    amount_paise = amount_int * 100
    # Create Razorpay Order
    order = razorpay_client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": '1',
    })
    # Get user info for sidebar/header
    db = Database()
    user_id = session.get('user_id')
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, email FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        user = {
            "name": row[0] if row else session.get('username', 'User'),
            "email": row[1] if row else "",
            "avatar_url": url_for('static', filename='avator.jpg')
        }
    return render_template(
        "checkout.html",
        order_id=order['id'],
        amount=amount_paise,
        KEY_ID=RAZORPAY_KEY_ID_TEST,
        user=user,
        order_details=booking_details
    )

@app.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')
    booking_details = request.form.get('booking')
    if not payment_id or not order_id or not signature or not booking_details:
        flash("Payment failed or incomplete data.", "danger")
        return redirect(url_for('payments'))
    # Verify signature
    booking = json.loads(json.loads(booking_details))
    print(type(booking))
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        print("Payment verification successful.")
        flash("Payment Successful!", "success")
        # Save payment details to database
        """        booking_details should contain:
                {
                    "parkingLot": {
                        "id": "1",
                        "name": "IGI Airport",
                        "rate": "25.0"
                    },
                    "slot": "PH2",
                    "vehicle": {
                        "id": "3",
                        "number": "DL4SAB1121",
                        "model": "Scorpio N"
                    },
                    "entryDateTime": "2025-06-14T16:55:00.000Z",
                    "exitDateTime": "2025-06-14T16:56:00.000Z",
                    "duration": 1,
                    "pricing": {
                        "hourlyRate": "25.0",
                        "subtotal": 25,
                        "tax": 5,
                        "total": 30
                    }
                }"""
        vehicle_ID = booking['vehicle']['id']
        slot = booking['slot']
        parking_lot_id = booking['parkingLot']['id']
        entry_time = datetime.strptime(booking['entryDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        duration = booking['duration'] #hours
        amount = booking['pricing']['total']
        exit_time = entry_time + timedelta(hours=duration)
        ticket_ID = generateTicketID(vehicle_ID,slot,parking_lot_id,entry_time,duration,exit_time,amount) # Generate a unique ticket ID
        db = Database()
        user_id = session.get('user_id')
        with db._connect() as conn:
            cursor = conn.cursor()
            # Insert payment record
            cursor.execute('''
                INSERT INTO payments (user_id, amount, status, method, transaction_id, ticket_id) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                amount,
                'SUCCESS',
                'Razorpay',
                payment_id,
                ticket_ID,
            ))
            conn.commit()
        return redirect(url_for('payments'))
    except Exception as e:
        flash("Payment Verification Failed.", "danger")
        print("Payment verification failed.")
        print(f"Error: {e}")
        db = Database()
        user_id = session.get('user_id')
        with db._connect() as conn:
            cursor = conn.cursor()
            # Insert failed payment record
            cursor.execute('''
                INSERT INTO payments (user_id, amount, status, method, transaction_id, ticket_id) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                booking['pricing']['total'],
                'FAILED',
                'Razorpay',
                payment_id,
                None  # No ticket ID for failed payments
            ))
            conn.commit()
        return redirect(url_for('payments'))
    
def createQR(ticketID):
    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ticketID)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    img_path = os.path.join('static','qr_codes',f'{ticketID}.png')
    img.save(img_path)
    return img_path

@app.route('/view_ticket/<booking_id>', methods=['GET'])
@login_required
def view_ticket(booking_id):
    db = Database()
    user_details = get_current_user_details()
    user_email = user_details['email'] if user_details else None
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets WHERE id=? AND owner_email=?', (booking_id, user_email))
        ticket = cursor.fetchone()
        if not ticket:
            flash("Ticket not found.", "danger")
            return redirect(url_for('my_bookings'))
        # Convert ticket data to a dictionary
        vehicle_number = None
        cursor.execute('SELECT number FROM vehicles WHERE id=?', (ticket[2],))
        vehicle = cursor.fetchone()
        if vehicle:
            vehicle_number = vehicle[0]
        parking_name = None
        cursor.execute('SELECT name FROM parkingspots WHERE id=?', (ticket[12],))
        parking_lot = cursor.fetchone()
        if parking_lot:
            parking_name = parking_lot[0]
        ticket_data = {
            "id": ticket[0],
            "code": ticket[1],
            "vehicle_id": vehicle_number,
            "owner_email": ticket[3],
            "epoch": ticket[4],
            "entry": bool(ticket[5]),
            "amount": ticket[8],
            "entry_epoch": ticket[6],
            "exit": bool(ticket[9]),
            "exit_epoch": ticket[7],
            "slot_no": ticket[10],
            "qr_path": ticket[11],
            "spot_id": parking_name
        }
    return json.dumps(ticket_data)

def generateTicketID(vehicle_id, slot, parking_lot_id, entry_time, duration, exit_time,amount):
    # Generate a unique ticket ID based on vehicle ID, slot, parking lot ID, and entry time
    #generate a randon ticket ID with UUID class and save it to database along with other feilds
    ticket_id = str(uuid.uuid4())
    user_details = get_current_user_details()
    if not user_details:
        raise Exception("User not logged in")
    email = user_details['email']
    db = Database()
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tickets (code, vehicle_id, owner_email, epoch, entry, amount,entry_epoch, exit, exit_epoch, comment, qr_path, spot_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticket_id,
            vehicle_id,
            email,
            int(time.time()),
            False,
            amount,
            int(entry_time.timestamp()),  # entry time in epoch
            False,
            int(exit_time.timestamp()),  # exit time in epoch
            slot,
            createQR(ticket_id),  # Generate QR code and save path
            parking_lot_id  # Assuming parking_lot_id is the spot_id            
        ))
        conn.commit()
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM tickets WHERE code=?', (ticket_id,))
        ticket_id_no = cursor.fetchone()
        if ticket_id_no:
            ticket_id_no = ticket_id_no[0]
            return ticket_id_no

@app.route('/checkTicket', methods=['POST'])
def checkTicket():
    data = request.form if request.form else request.json()
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        return jsonify({"error": "Ticket ID is required"}), 400
    db = Database()
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets WHERE code=?', (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        # Convert ticket data to a dictionary
        vehicle_number = None
        cursor.execute('SELECT number FROM vehicles WHERE id=?', (ticket[2],))
        vehicle = cursor.fetchone()
        if vehicle:
            vehicle_number = vehicle[0]
        parking_name = None
        cursor.execute('SELECT name FROM parkingspots WHERE id=?', (ticket[12],))
        parking_lot = cursor.fetchone()
        if parking_lot:
            parking_name = parking_lot[0]
        ticket_data = {
            "id": ticket[0],
            "code": ticket[1],
            "vehicle_id": vehicle_number,
            "owner_email": ticket[3],
            "epoch": ticket[4],
            "entry": bool(ticket[5]),
            "amount": ticket[8],
            "entry_epoch": ticket[6],
            "exit": bool(ticket[9]),
            "exit_epoch": ticket[7],
            "slot_no": ticket[10],
            "qr_path": ticket[11],
            "spot_id": parking_name
        }
    return jsonify(ticket_data)

@app.route('/makeEntry', methods=['POST'])
def makeEntry():
    data = request.form if request.form else request.json()
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        return jsonify({"error": "Ticket ID is required"}), 400
    db = Database()
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets WHERE code=?', (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        if ticket[5]:  # If entry is already made
            return jsonify({"error": "Entry already made for this ticket"}), 400
        # Update ticket entry status
        cursor.execute('''
            UPDATE tickets SET entry=?, entry_epoch=? WHERE code=?
        ''', (True, int(time.time()), ticket_id))
        conn.commit()
        return jsonify({"message": "Entry made successfully", "ticket_id": ticket_id})

@app.route('/makeExit', methods=['POST'])
def makeExit():
    data = request.form if request.form else request.json()
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        return jsonify({"error": "Ticket ID is required"}), 400
    db = Database()
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets WHERE code=?', (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        if not ticket[5]:
            return jsonify({"error": "Entry not made for this ticket"}), 400
        if ticket[9]:
            return jsonify({"error": "Exit already made for this ticket"}), 400
        # Update ticket exit status
        cursor.execute('''
            UPDATE tickets SET exit=?, exit_epoch=? WHERE code=?
        ''', (True, int(time.time()), ticket_id))   
        conn.commit()
        return jsonify({"message": "Exit made successfully", "ticket_id": ticket_id})

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)



