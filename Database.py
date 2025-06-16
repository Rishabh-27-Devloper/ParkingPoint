import sqlite3
import secrets
import time
from flask import Flask, send_from_directory
import os

class Database:
    def __init__(self, db_path='parking_manager.db'):
        self.db_path = db_path
        self._create_user_table()
        self._create_vehicle_table()
        self._create_ticket_table()
        self._create_notification_table()
        self._create_parking_spots_table()
        self._create_payment_table()

    def _create_dummy_entries(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            # Insert dummy users
            cursor.execute('INSERT INTO payments (user_id, amount, status, method, transaction_id, ticket_id) VALUES (?, ?, ?, ?, ?, ?)',
                           (1, 100.0, 'SUCCESS', 'Credit Card', 'txn_123456',1))
            cursor.execute('INSERT INTO payments (user_id, amount, status, method, transaction_id, ticket_id) VALUES (?, ?, ?, ?, ?, ?)',
                           (2, 50.0, 'PENDING', 'PayPal', 'txn_654321',2))
            cursor.execute('INSERT INTO payments (user_id, amount, status, method, transaction_id, ticket_id) VALUES (?, ?, ?, ?, ?, ?)',
                           (3, 75.0, 'FAILED', 'Bank Transfer', 'txn_789012',3))
            cursor.execute('INSERT INTO tickets (code, vehicle_id, owner_email, epoch, entry, amount, exit, exit_epoch, comment, qr_path, spot_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           ('TICKET123', 3, 'r0207shukla@gmail.com', int(time.time()), True, 100.0, False, None, 'First ticket', '/path/to/qr1.png', 1))
            cursor.execute('INSERT INTO tickets (code, vehicle_id, owner_email, epoch, entry, amount, exit, exit_epoch, comment, qr_path, spot_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           ('TICKET456', 3, 'r0207shukla@gmail.com', int(time.time()), True, 50.0, False, None, 'Second ticket', '/path/to/qr2.png', 2))
            cursor.execute('INSERT INTO tickets (code, vehicle_id, owner_email, epoch, entry, amount, exit, exit_epoch, comment, qr_path, spot_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           ('TICKET789', 3, 'r0207shukla@gmail.com', int(time.time()), True, 50.0, False, None, 'Third ticket', '/path/to/qr2.png', 3))
    def _delete_dummy_entries(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM payments')
            cursor.execute('DELETE FROM tickets')
            conn.commit()
    
    def _create_payment_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    method TEXT NOT NULL,
                    transaction_id TEXT UNIQUE,
                    ticket_id INTEGER,
                    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()

    def _create_vehicle_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    model TEXT NOT NULL,
                    number TEXT UNIQUE NOT NULL,
                    color TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()


    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _reset_database(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            # cursor.execute('DROP TABLE IF EXISTS users')
            # cursor.execute('DROP TABLE IF EXISTS vehicles')
            # cursor.execute('DROP TABLE IF EXISTS notifications')
            # cursor.execute('DROP TABLE IF EXISTS parkingspots')
            cursor.execute('DROP TABLE IF EXISTS payments')
            cursor.execute('DROP TABLE IF EXISTS tickets')
            # cursor.execute('DROP TABLE IF EXISTS tickets')
            conn.commit()
        self._create_user_table()
        self._create_vehicle_table()
        self._create_notification_table()
        self._create_ticket_table()
        self._create_parking_spots_table()
        self._create_payment_table()

    def _create_user_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE,
                    email_notifications BOOLEAN DEFAULT 0,
                    sms_notifications BOOLEAN DEFAULT 0,
                    language TEXT,
                    private_profile BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()

    def _create_ticket_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    vehicle_id INTEGER,
                    owner_email TEXT,
                    epoch INTEGER,
                    entry BOOLEAN DEFAULT 0,
                    entry_epoch INTEGER DEFAULT 0,
                    exit_epoch INTEGER DEFAULT 0,
                    amount REAL DEFAULT 0,
                    exit BOOLEAN DEFAULT 0,
                    comment TEXT,
                    qr_path TEXT,
                    spot_id INTEGER,
                    FOREIGN KEY(spot_id) REFERENCES parkingspots(id),
                    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
                    FOREIGN KEY(owner_email) REFERENCES users(email)
                )
            ''')
            conn.commit()
    def _create_parking_spots_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parkingspots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    locality TEXT NOT NULL,
                    coordinates TEXT NOT NULL,
                    capacity INTEGER NOT NULL,
                    rate REAL NOT NULL,
                    status TEXT DEFAULT 'Available'
                )
            ''')
            conn.commit()

    def _create_notification_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    seen BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()

    # User management (existing methods unchanged)
    def insert_user(self, username, password, email=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, password, email)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def update_user(self, user_id, username=None, password=None, email=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            if username:
                fields.append('username=?')
                values.append(username)
            if password:
                fields.append('password=?')
                values.append(password)
            if email:
                fields.append('email=?')
                values.append(email)
            values.append(user_id)
            if fields:
                cursor.execute(
                    f'UPDATE users SET {", ".join(fields)} WHERE id=?',
                    tuple(values)
                )
                conn.commit()
                return cursor.rowcount > 0
            return False

    def delete_user(self, user_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def check_login(self, username, password):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM users WHERE username=? AND password=?',
                (username, password)
            )
            return cursor.fetchone() is not None

    def signup_user(self, username, password, email=None):
        return self.insert_user(username, password, email)

    # Vehicle management
    def register_vehicle(self, owner_email, vehicle_number, vehicle_type=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO vehicles (owner_email, vehicle_number, vehicle_type) VALUES (?, ?, ?)',
                    (owner_email, vehicle_number, vehicle_type)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_vehicles_by_owner(self, owner_email):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM vehicles WHERE owner_email=?',
                (owner_email,)
            )
            return cursor.fetchall()

    def get_vehicle_by_number(self, vehicle_number):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM vehicles WHERE vehicle_number=?',
                (vehicle_number,)
            )
            return cursor.fetchone()

    # Ticket/QR management
    def create_ticket(self, vehicle_id, owner_email, comment=None, qr_path=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            code = self._generate_unique_code(cursor)
            epoch = int(time.time())
            try:
                cursor.execute(
                    '''INSERT INTO tickets (code, vehicle_id, owner_email, epoch, entry, comment, qr_path)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (code, vehicle_id, owner_email, epoch, False, comment, qr_path)
                )
                conn.commit()
                return code
            except sqlite3.IntegrityError:
                return None

    def _generate_unique_code(self, cursor):
        while True:
            code = secrets.token_urlsafe(4)
            cursor.execute("SELECT * FROM tickets WHERE code=?", (code,))
            if not cursor.fetchone():
                return code

    def get_ticket_by_code(self, code):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tickets WHERE code=?', (code,))
            return cursor.fetchone()

    def update_ticket_entry(self, code, entry=True):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tickets SET entry=? WHERE code=?',
                (entry, code)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_all_tickets(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tickets')
            return cursor.fetchall()

    def get_tickets_by_owner(self, owner_email):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tickets WHERE owner_email=?', (owner_email,))
            return cursor.fetchall()
    def get_user_list(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            return cursor.fetchall()


if __name__ == "__main__":
    db = Database()
    with db._connect() as conn:
        cursor = conn.cursor()
        # Uncomment to reset the database and create dummy entries
        # db._reset_database()
        # db._create_dummy_entries()
        # db._delete_dummy_entries()
        print("users->")
        cursor.execute('SELECT * FROM users')
        print(cursor.fetchall())
        print("payments->")
        cursor.execute('SELECT * FROM payments')
        print(cursor.fetchall())
        print("tickets->")
        cursor.execute('SELECT * FROM tickets')
        print(cursor.fetchall())