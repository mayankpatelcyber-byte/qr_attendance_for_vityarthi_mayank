import os
import sqlite3
import socket
import base64
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

# DB CONFIG
DB_FILE = "classroom_attendance.db"

def init_db():
    """Sets up the SQLite tables and populates some dummy data."""
    d = sqlite3.connect(DB_FILE)
    c = d.cursor()

    # Schema
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        reg_no TEXT UNIQUE NOT NULL,
        phone_number TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id)
    );
    """)
    d.commit()

    # Seeds
    c.execute("SELECT count(*) FROM students;")
    if c.fetchone()[0] == 0:
        seeds = [
            ("Aarav Sharma", "2024CS101", "9876543210", "Computer Science"),
            ("Ananya Verma", "2024CS102", "9812345678", "Computer Science"),
            ("Rohan Deshmukh", "2024CS103", "9765432109", "Computer Science"),
            ("Priya Iyer", "2024CS104", "9923456789", "Information Tech"),
            ("Vikram Malhotra", "2024CS105", "9834567890", "Computer Science"),
            ("Sneha Patel", "2024CS106", "9745678901", "Computer Science"),
            ("Kabir Khan", "2024CS107", "9856789012", "AI & Data Science"),
        ]
        c.executemany("INSERT INTO students (name, reg_no, phone_number, department) VALUES (?, ?, ?, ?);", seeds)
        d.commit()
        print(f"✅ Seeded {len(seeds)} students.")
    d.close()

def lookup_by_phone(mob):
    """Finds a student record by phone number."""
    digits = "".join(c for c in mob if c.isdigit())
    # Keep last 10 digits
    key = digits[-10:] if (len(digits) >= 10) else digits
    
    d = sqlite3.connect(DB_FILE)
    d.row_factory = sqlite3.Row
    c = d.cursor()
    c.execute("SELECT * FROM students WHERE phone_number LIKE ?;", (f"%{key}",))
    stu = c.fetchone()
    d.close()
    return dict(stu) if stu else None

def mark_att(uid):
    """Logs attendance for a specific student ID."""
    today = datetime.now().strftime("%Y-%m-%d")
    ts = datetime.now().strftime("%I:%M:%S %p")
    
    d = sqlite3.connect(DB_FILE)
    c = d.cursor()
    c.execute("SELECT id FROM attendance WHERE student_id = ? AND date = ?;", (uid, today))
    if c.fetchone():
        d.close()
        return False, "Already marked today."
        
    c.execute("INSERT INTO attendance (student_id, date, timestamp) VALUES (?, ?, ?);", (uid, today, ts))
    d.commit()
    d.close()
    return True, ts

def get_live_entries():
    """Grabs everyone checked in today."""
    today = datetime.now().strftime("%Y-%m-%d")
    d = sqlite3.connect(DB_FILE)
    d.row_factory = sqlite3.Row
    c = d.cursor()
    c.execute("""
    SELECT s.name, s.reg_no, s.phone_number, s.department, a.timestamp
    FROM attendance a JOIN students s ON a.student_id = s.id WHERE a.date = ? ORDER BY a.id DESC;
    """, (today,))
    rows = c.fetchall()
    d.close()
    return [dict(r) for r in rows]

def get_total():
    d = sqlite3.connect(DB_FILE)
    c = d.cursor()
    c.execute("SELECT count(*) FROM students;")
    cnt = c.fetchone()[0]
    d.close()
    return cnt

# WEB UTILS
def get_ip():
    """Finds the local IP for the phone to use."""
    # Try Google DNS
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.8)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except:
        pass

    # Try hostname
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                return ip
    except:
        pass
    
    # Fallback
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except:
        pass
        
    return "127.0.0.1"

def make_qr(target):
    """Generates a base64 string for the QR image."""
    import qrcode
    q = qrcode.QRCode(version=1, box_size=8, border=2)
    q.add_data(target)
    q.make(fit=True)
    img = q.make_image(fill_color