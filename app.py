from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from calendar import monthrange

app = Flask(__name__)
app.secret_key = 'supersecret'
DATABASE = 'users.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            start TEXT,
            end TEXT,
            break_start TEXT,
            break_end TEXT
        )''')
init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        try:
            with get_db() as db:
                db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            return redirect('/login')
        except:
            return 'Username existiert schon!'
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                return redirect('/')
        return 'Falsche Login-Daten!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    if 'user_id' not in session:
        return jsonify({})
    with get_db() as db:
        rows = db.execute('SELECT * FROM entries WHERE user_id = ?', (session['user_id'],)).fetchall()
        data = {row['date']: {
            'start': row['start'],
            'end': row['end'],
            'breakStart': row['break_start'],
            'breakEnd': row['break_end']
        } for row in rows}
        return jsonify(data)

@app.route('/api/entries/<date>', methods=['POST'])
def save_entry(date):
    if 'user_id' not in session:
        return 'Not logged in', 403
    data = request.json
    with get_db() as db:
        db.execute('DELETE FROM entries WHERE user_id = ? AND date = ?', (session['user_id'], date))
        db.execute('''INSERT INTO entries (user_id, date, start, end, break_start, break_end)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (session['user_id'], date, data['start'], data['end'], data['breakStart'], data['breakEnd']))
    return '', 204

@app.route('/api/entries/<date>', methods=['DELETE'])
def delete_entry(date):
    if 'user_id' not in session:
        return 'Not logged in', 403
    with get_db() as db:
        db.execute('DELETE FROM entries WHERE user_id = ? AND date = ?', (session['user_id'], date))
    return '', 204

@app.route('/sum')
def sum_page():
    if 'user_id' not in session:
        return redirect('/login')

    month_str = request.args.get('month')
    if not month_str:
        month_str = datetime.now().strftime('%Y-%m')

    year, month = map(int, month_str.split('-'))
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, monthrange(year, month)[1])

    with get_db() as db:
        rows = db.execute('''
            SELECT date, start, end, break_start, break_end
            FROM entries
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (session['user_id'], first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'))).fetchall()

    daily_entries = []
    total_work_minutes = 0
    total_break_minutes = 0
    total_netto_minutes = 0

    for row in rows:
        try:
            start = datetime.strptime(row['start'], '%H:%M')
            end = datetime.strptime(row['end'], '%H:%M')
            break_start = datetime.strptime(row['break_start'], '%H:%M')
            break_end = datetime.strptime(row['break_end'], '%H:%M')

            work_duration = (end - start).total_seconds() / 60
            break_duration = (break_end - break_start).total_seconds() / 60
            netto_duration = max(work_duration - break_duration, 0)

            total_work_minutes += work_duration
            total_break_minutes += break_duration
            total_netto_minutes += netto_duration

            daily_entries.append({
                'date': row['date'],
                'work_duration': f"{int(work_duration // 60)}h {int(work_duration % 60)}m",
                'break_duration': f"{int(break_duration // 60)}h {int(break_duration % 60)}m",
                'netto_duration': f"{int(netto_duration // 60)}h {int(netto_duration % 60)}m",
            })
        except:
            # falls ungültige Zeiten
            pass

    def fmt_time(total_minutes):
        h = int(total_minutes // 60)
        m = int(total_minutes % 60)
        return f"{h}h {m}m"

    return render_template('sum.html',
                           daily_entries=daily_entries,
                           hours=int(total_netto_minutes // 60),
                           minutes=int(total_netto_minutes % 60),
                           total_work=fmt_time(total_work_minutes),
                           total_break=fmt_time(total_break_minutes),
                           total_netto=fmt_time(total_netto_minutes),
                           selected_month=month_str)

if __name__ == '__main__':
    app.run(debug=True)
import os
from flask import Flask

app = Flask(__name__)

# ... dein restlicher Code ...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
