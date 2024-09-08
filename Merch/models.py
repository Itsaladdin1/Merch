import sqlite3
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.dialects.sqlite import JSON

db = SQLAlchemy()

def init_db():
    with sqlite3.connect('merch.db') as conn:
        c = conn.cursor()

        # Create tables if they don't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS merchandise (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                information TEXT NOT NULL,
                value REAL NOT NULL,
                specification TEXT NOT NULL,
                image_file TEXT NOT NULL DEFAULT 'default.jpg',
                category TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchandise_id INTEGER,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(merchandise_id) REFERENCES merchandise(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS sold (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchandise_id INTEGER,
                user_id INTEGER,
                quantity INTEGER NOT NULL,
                date_sold TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(merchandise_id) REFERENCES merchandise(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS discount (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                percentage REAL NOT NULL,
                category TEXT NOT NULL
            )
        ''')

        # Add the new column if it doesn't exist
        try:
            c.execute('ALTER TABLE discount ADD COLUMN usage_count INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            # If the column already exists, an OperationalError will be raised.
            pass

        conn.commit()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # Relationship to 'Sold'
    sold_records = db.relationship('Sold', back_populates='user')

class Information(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Changed to nullable=True for optional reference

class Merchandise(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    information = Column(Text, nullable=False)
    value = Column(Float, nullable=False)
    specification = Column(Text, nullable=False)
    image_file = Column(String(20), nullable=False, default='default.jpg')
    date_added = Column(DateTime, default=datetime.utcnow)
    sold_items = db.relationship('Sold', back_populates='merchandise')
    cart_items = db.relationship('CartItem', back_populates='merchandise')
    category = db.Column(JSON, nullable=False)
    color = db.Column(JSON, nullable=False)
    size = db.Column(JSON, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchandise_id = db.Column(db.Integer, db.ForeignKey('merchandise.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    merchandise = db.relationship('Merchandise', back_populates='cart_items')

class Sold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchandise_id = db.Column(db.Integer, db.ForeignKey('merchandise.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Ensure nullable=False
    quantity = db.Column(db.Integer, nullable=False)
    date_sold = db.Column(db.DateTime, default=datetime.utcnow)

    merchandise = db.relationship('Merchandise', back_populates='sold_items')
    user = db.relationship('User', back_populates='sold_records')

class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    usage_count = db.Column(db.Integer, default=0)  # Track how many times the discount is used
