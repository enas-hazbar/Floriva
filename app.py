from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv


#  Load environment variables
load_dotenv()

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
    

app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret')

# Database configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'Floriva')

mysql = MySQL(app)

#ROUTES#

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


#Test DB connection
@app.route('/test_db')
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        cursor.close()
        return f"✅ Database connected successfully!<br>Tables: {tables}"
    except Exception as e:
        return f"❌ Database connection failed:<br>{e}"


@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        date_obj = datetime.strptime(value, "%Y-%m-%d")
        return date_obj.strftime("%d-%m-%Y")
    except Exception:
        try:
            # for "YYYY-%m" month format
            date_obj = datetime.strptime(value, "%Y-%m")
            return date_obj.strftime("%m-%Y")
        except Exception:
            return value
        
@app.template_filter('weekformat')
def weekformat(value):
    """
    Convert '2025-W43' → 'Week 43 2025'
    """
    try:
        year, week_str = value.split('-W')
        return f" {int(week_str)} {year}"
    except Exception:
        return value    
# Register new user
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    surname = request.form['surname']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    telephone = request.form['telephone']
    greenhouse = request.form['greenhouse_name']

    if not all([name, surname, username, password, email, telephone, greenhouse]):
        return render_template('index.html', error="All fields are required.")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if username already exists
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        return render_template('index.html', error="This username is already taken.")

    # Hash the password before saving
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert new user into the database
    cursor.execute("""
        INSERT INTO users (name, surname, username, password, email, telephone, greenhouse_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, surname, username, hashed_password, email, telephone, greenhouse))
    mysql.connection.commit()

    cursor.execute("SELECT id, username FROM users WHERE username = %s", (username,))
    new_user = cursor.fetchone()
    cursor.close()
    session['logged_in'] = True
    session['user_id'] = new_user['id']
    session['username'] = new_user['username']
    return redirect(url_for('dashboard_filter'))

#User login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return {"ok": False, "error": "Please enter both username and password."}, 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    #Get all usernames (to check if username exists at all)
    cursor.execute("SELECT username FROM users")
    all_users = [row['username'] for row in cursor.fetchall()]
    cursor.close()

    # ✅ Case 1: Username not in database
    if username not in all_users:
        return {"ok": False, "error": "Username and password are incorrect."}

    # ✅ Case 2: Username exists but not found in query 
    if not user:
        return {"ok": False, "error": "Username not found."}

    # ✅ Case 3: Wrong password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return {"ok": False, "error": "Incorrect password."}

    # ✅ Case 4: Successful login
    session['logged_in'] = True
    session['user_id'] = user['id']
    session['username'] = user['username']

    return {"ok": True, "redirect": url_for('dashboard_filter')}

#logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

#Add sensor for user
@app.route('/add_device', methods=['POST'])
def add_device():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    device_name = request.form.get('device_name', '').strip()
    if not device_name:
        return {"ok": False, "error": "Device name is required."}, 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "INSERT INTO devices (user_id, device_name, created_at) VALUES (%s, %s, NOW())",
        (user_id, device_name)
    )
    mysql.connection.commit()
    new_device_id = cursor.lastrowid
    cursor.close()

    #write it to a small file that your serial script can read
    device_id_path = os.path.join(os.path.dirname(__file__), "device_id.txt")
    try:
        with open(device_id_path, "w") as f:
            f.write(str(new_device_id))
        print(f"✅ device_id.txt written with ID {new_device_id}")
    except Exception as e:
        print("⚠️ Could not write device_id.txt:", e)
    return redirect(url_for('dashboard_filter'))

# Arduino → Flask Data Upload
@app.route('/upload_data', methods=['POST'])
def upload_data():
    data = request.get_json(force=True)
    print("📦 Received data:", data)

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO data (device_id, date, day_name, period, temperature, humidity, voltage, lights, timestamp)
        VALUES (%s, CURDATE(), DAYNAME(CURDATE()), %s, %s, %s, %s, %s, NOW())
    """, (
        data.get('device_id'),
        data.get('period'),
        data.get('temperature'),
        data.get('humidity'),
        data.get('voltage'),
        data.get('lights')
    ))
    mysql.connection.commit()
    cursor.close()

    print("✅ Data saved successfully.")
    return {"status": "success"}
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

#Dashboard
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard_filter():
    user_id = session.get('user_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, device_name FROM devices WHERE user_id = %s", (user_id,))
    devices = cursor.fetchall()
    if not devices:
        return render_template(
            'dashboard.html',
            data=[],
            stats=None,
            devices=[],
            view_type='day',
            selected_date=datetime.today().strftime('%Y-%m-%d'),
            prev_date=None,
            next_date=None,
            username=session.get('username')
        )

    # Collect all device IDs for this user
    device_ids = tuple(d['id'] for d in devices)

    # Handle view types
    view_type = request.args.get('view', 'day')
    selected_date = request.args.get('date')
    today = datetime.today()
    if view_type == 'week':
        if not selected_date:
            iso = today.isocalendar()
            selected_date = f"{iso.year}-W{iso.week:02d}"
        try:
            year_str, week_str = selected_date.split('-W')
            year, week = int(year_str), int(week_str)
            date_obj = datetime.fromisocalendar(year, week, 1)
        except Exception:
            iso = today.isocalendar()
            selected_date = f"{iso.year}-W{iso.week:02d}"
            date_obj = datetime.fromisocalendar(iso.year, iso.week, 1)
    elif view_type == 'month':
        if not selected_date:
            selected_date = today.strftime('%Y-%m')
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m')
        except Exception:
            date_obj = today.replace(day=1)
            selected_date = date_obj.strftime('%Y-%m')
    else:
        if not selected_date:
            selected_date = today.strftime('%Y-%m-%d')
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        except Exception:
            date_obj = today
            selected_date = date_obj.strftime('%Y-%m-%d')

    # ---  DAY VIEW ---
    if view_type == 'day':
        cursor.execute("""
            SELECT 
                TRIM(period) AS period,
                (SELECT temperature 
                 FROM data d2 
                 WHERE d2.period = d1.period 
                   AND d2.date = d1.date 
                   AND d2.device_id IN %s
                 ORDER BY d2.timestamp DESC 
                 LIMIT 1) AS temperature,
                (SELECT humidity 
                 FROM data d3 
                 WHERE d3.period = d1.period 
                   AND d3.date = d1.date 
                   AND d3.device_id IN %s
                 ORDER BY d3.timestamp DESC 
                 LIMIT 1) AS humidity,
                (SELECT voltage
                 FROM data d4
                 WHERE d4.period = d1.period
                   AND d4.date = d1.date
                   AND d4.device_id IN %s
                 ORDER BY d4.timestamp DESC
                 LIMIT 1) AS voltage,
                SUBSTRING_INDEX(GROUP_CONCAT(lights ORDER BY id DESC), ',', 1) AS lights,
                date
            FROM data d1
            WHERE date = %s AND device_id IN %s
            GROUP BY period, date
            ORDER BY FIELD(period, 'Morning', 'Afternoon', 'Evening')
        """, (device_ids, device_ids, device_ids, date_obj.strftime('%Y-%m-%d'), device_ids))
        data = cursor.fetchall()

        cursor.execute("""
            SELECT 
                MIN(temperature) AS low_temp,
                MAX(temperature) AS high_temp,
                MIN(humidity) AS low_hum,
                MAX(humidity) AS high_hum,
                ROUND(AVG(voltage), 2) AS avg_voltage
            FROM data 
            WHERE date = %s AND device_id IN %s
        """, (date_obj.strftime('%Y-%m-%d'), device_ids))
        stats = cursor.fetchone()

    # ---  WEEK VIEW ---
    elif view_type == 'week':
        week_anchor = date_obj.date()
        cursor.execute("""
            SELECT DATE_FORMAT(date, '%%Y-%%m-%%d') AS date,
                   ROUND(AVG(temperature), 2) AS avg_temp,
                   ROUND(AVG(humidity), 2) AS avg_hum,
                   ROUND(AVG(voltage), 2) AS avg_voltage,
                   ROUND(SUM(lights = 'ON') / COUNT(*) * 100, 1) AS lights_on_pct
            FROM data
            WHERE YEARWEEK(date, 3) = YEARWEEK(%s, 3)
              AND device_id IN %s
            GROUP BY date
            ORDER BY date ASC
        """, (week_anchor, device_ids))
        data = cursor.fetchall()

        cursor.execute("""
            SELECT 
                MIN(temperature) AS low_temp,
                MAX(temperature) AS high_temp,
                MIN(humidity) AS low_hum,
                MAX(humidity) AS high_hum,
                ROUND(AVG(voltage), 2) AS avg_voltage
            FROM data
            WHERE YEARWEEK(date, 3) = YEARWEEK(%s, 3)
              AND device_id IN %s
        """, (week_anchor, device_ids))
        stats = cursor.fetchone()

        iso = date_obj.isocalendar()
        selected_date = f"{iso.year}-W{iso.week:02d}"

    # ---  MONTH VIEW ---
    else:
        month_anchor = date_obj.date()
        cursor.execute("""
            SELECT DATE_FORMAT(date, '%%Y-%%m-%%d') AS date,
                   ROUND(AVG(temperature), 2) AS avg_temp,
                   ROUND(AVG(humidity), 2) AS avg_hum,
                   ROUND(AVG(voltage), 2) AS avg_voltage,
                   ROUND(SUM(lights = 'ON') / COUNT(*) * 100, 1) AS lights_on_pct
            FROM data
            WHERE MONTH(date) = MONTH(%s)
              AND YEAR(date) = YEAR(%s)
              AND device_id IN %s
            GROUP BY date
            ORDER BY date ASC
        """, (month_anchor, month_anchor, device_ids))
        data = cursor.fetchall()

        cursor.execute("""
            SELECT 
                MIN(temperature) AS low_temp,
                MAX(temperature) AS high_temp,
                MIN(humidity) AS low_hum,
                MAX(humidity) AS high_hum,
                ROUND(AVG(voltage), 2) AS avg_voltage
            FROM data
            WHERE MONTH(date) = MONTH(%s)
              AND YEAR(date) = YEAR(%s)
              AND device_id IN %s
        """, (month_anchor, month_anchor, device_ids))
        stats = cursor.fetchone()

        selected_date = date_obj.strftime('%Y-%m')

    # --- Next and pervious ---
    if view_type == 'day':
        prev_date = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    elif view_type == 'week':
        prev_iso = (date_obj - timedelta(days=7)).isocalendar()
        next_iso = (date_obj + timedelta(days=7)).isocalendar()
        prev_date = f"{prev_iso.year}-W{prev_iso.week:02d}"
        next_date = f"{next_iso.year}-W{next_iso.week:02d}"
    else:
        prev_month = (date_obj.replace(day=1) - timedelta(days=1)).replace(day=1)
        next_month = (date_obj.replace(day=28) + timedelta(days=4)).replace(day=1)
        prev_date = prev_month.strftime('%Y-%m')
        next_date = next_month.strftime('%Y-%m')

    cursor.close()
    if not data:
        return render_template(
            'dashboard.html',
            data=[],
            stats=None,
            devices=devices,
            view_type=view_type,
            selected_date=selected_date,
            prev_date=prev_date,
            next_date=next_date,
            username=session.get('username')
        )

    return render_template(
        'dashboard.html',
        data=data,
        stats=stats,
        devices=devices,
        view_type=view_type,
        selected_date=selected_date,
        prev_date=prev_date,
        next_date=next_date,
        username=session.get('username')
    )

@app.route('/check_username')
def check_username():
    username = request.args.get('username', '').strip()
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return "taken" if exists else "free"

if __name__ == '__main__':
    app.run(debug=True)
