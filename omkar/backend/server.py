from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import get_db, init_db
import bcrypt
import jwt
import datetime
import os

FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=FRONTEND, static_url_path='')
CORS(app, resources={r'/api/*': {'origins': '*'}})
SECRET = os.environ.get('JWT_SECRET', 'blooddrop_secret_key')

init_db()

@app.route('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND, filename)

# ── helpers ───────────────────────────────────────────────────────────────────

def make_token(payload):
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    return jwt.encode(payload, SECRET, algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, SECRET, algorithms=['HS256'])

def current_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, None
    try:
        data = decode_token(auth.split(' ')[1])
        return data.get('id'), data.get('role')
    except Exception:
        return None, None

def require_role(role):
    uid, r = current_user()
    if not uid or r != role:
        return None, None, (jsonify({'message': 'Unauthorized'}), 401)
    return uid, r, None

def err(msg, code=400):
    return jsonify({'message': msg}), code

def get_cursor(conn):
    return conn.cursor(dictionary=True)

def row(conn, sql, params=()):
    cur = get_cursor(conn)
    cur.execute(sql, params)
    result = cur.fetchone()
    cur.close()
    return result or {}

def rows(conn, sql, params=()):
    cur = get_cursor(conn)
    cur.execute(sql, params)
    result = cur.fetchall()
    cur.close()
    return result

def scalar(conn, sql, params=()):
    cur = get_cursor(conn)
    cur.execute(sql, params)
    result = cur.fetchone()
    cur.close()
    return list(result.values())[0] if result else 0

def execute(conn, sql, params=()):
    cur = get_cursor(conn)
    cur.execute(sql, params)
    lastid = cur.lastrowid
    cur.close()
    return lastid

# ── donor auth ────────────────────────────────────────────────────────────────

@app.route('/api/donor/register', methods=['POST'])
def donor_register():
    d = request.json
    if not all([d.get('name'), d.get('email'), d.get('password'), d.get('blood_group')]):
        return err('Name, email, blood group and password are required')
    hashed = bcrypt.hashpw(d['password'].encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        lastid = execute(conn,
            "INSERT INTO donors (name,email,password,phone,blood_group,city,state,age,weight) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d['name'], d['email'], hashed, d.get('phone'), d['blood_group'],
             d.get('city'), d.get('state'), d.get('age') or None, d.get('weight') or None))
        conn.commit()
        donor = row(conn, "SELECT * FROM donors WHERE id=%s", (lastid,))
        donor.pop('password', None)
        token = make_token({'id': donor['id'], 'role': 'donor'})
        return jsonify({'token': token, 'donor': donor}), 201
    except Exception as e:
        return err('Email already registered' if '1062' in str(e) else str(e))
    finally:
        conn.close()

@app.route('/api/donor/login', methods=['POST'])
def donor_login():
    d = request.json
    conn = get_db()
    donor = row(conn, "SELECT * FROM donors WHERE email=%s", (d.get('email'),))
    conn.close()
    if not donor or not bcrypt.checkpw(d.get('password', '').encode(), donor['password'].encode()):
        return err('Invalid email or password', 401)
    donor.pop('password')
    token = make_token({'id': donor['id'], 'role': 'donor'})
    return jsonify({'token': token, 'donor': donor})

# ── donor profile & donations ─────────────────────────────────────────────────

@app.route('/api/donor/profile', methods=['GET', 'PUT'])
def donor_profile():
    uid, _, e = require_role('donor')
    if e: return e
    conn = get_db()
    if request.method == 'GET':
        donor = row(conn, "SELECT * FROM donors WHERE id=%s", (uid,))
        conn.close()
        donor.pop('password', None)
        return jsonify(donor)
    d = request.json
    execute(conn,
        "UPDATE donors SET phone=COALESCE(%s,phone), city=COALESCE(%s,city), state=COALESCE(%s,state), "
        "age=COALESCE(%s,age), weight=COALESCE(%s,weight), "
        "is_available=COALESCE(%s,is_available), last_donation=COALESCE(%s,last_donation) WHERE id=%s",
        (d.get('phone'), d.get('city'), d.get('state'), d.get('age') or None,
         d.get('weight') or None,
         1 if d.get('is_available') is True else 0 if d.get('is_available') is False else None,
         d.get('last_donation') or None, uid))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Profile updated'})

@app.route('/api/donor/donations', methods=['GET'])
def donor_donations():
    uid, _, e = require_role('donor')
    if e: return e
    conn = get_db()
    data = rows(conn,
        "SELECT d.*, h.name AS hospital_name, h.city AS hospital_city "
        "FROM donations d JOIN hospitals h ON d.hospital_id=h.id "
        "WHERE d.donor_id=%s ORDER BY d.donation_date DESC", (uid,))
    conn.close()
    return jsonify(data)

# ── hospital auth ─────────────────────────────────────────────────────────────

@app.route('/api/hospital/register', methods=['POST'])
def hospital_register():
    d = request.json
    required = ['name', 'email', 'password', 'phone', 'license_no', 'city', 'state']
    if not all(d.get(k) for k in required):
        return err('All required fields must be filled')
    hashed = bcrypt.hashpw(d['password'].encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        lastid = execute(conn,
            "INSERT INTO hospitals (name,email,password,phone,license_no,address,city,state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (d['name'], d['email'], hashed, d['phone'], d['license_no'],
             d.get('address'), d['city'], d['state']))
        conn.commit()
        hospital = row(conn, "SELECT * FROM hospitals WHERE id=%s", (lastid,))
        hospital.pop('password', None)
        token = make_token({'id': hospital['id'], 'role': 'hospital'})
        return jsonify({'token': token, 'hospital': hospital}), 201
    except Exception as e:
        return err('Email or license already registered' if '1062' in str(e) else str(e))
    finally:
        conn.close()

@app.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    d = request.json
    conn = get_db()
    hospital = row(conn, "SELECT * FROM hospitals WHERE email=%s", (d.get('email'),))
    conn.close()
    if not hospital or not bcrypt.checkpw(d.get('password', '').encode(), hospital['password'].encode()):
        return err('Invalid email or password', 401)
    hospital.pop('password')
    token = make_token({'id': hospital['id'], 'role': 'hospital'})
    return jsonify({'token': token, 'hospital': hospital})

# ── hospital profile ──────────────────────────────────────────────────────────

@app.route('/api/hospital/profile', methods=['GET'])
def hospital_profile():
    uid, _, e = require_role('hospital')
    if e: return e
    conn = get_db()
    h = row(conn, "SELECT * FROM hospitals WHERE id=%s", (uid,))
    conn.close()
    h.pop('password', None)
    return jsonify(h)

# ── hospital requests ─────────────────────────────────────────────────────────

@app.route('/api/hospital/requests', methods=['GET', 'POST'])
def hospital_requests():
    uid, _, e = require_role('hospital')
    if e: return e
    conn = get_db()
    if request.method == 'GET':
        data = rows(conn,
            "SELECT r.*, h.name AS hospital_name, h.city, h.state, h.phone "
            "FROM blood_requests r JOIN hospitals h ON r.hospital_id=h.id "
            "WHERE r.hospital_id=%s ORDER BY r.created_at DESC", (uid,))
        conn.close()
        return jsonify(data)
    d = request.json
    execute(conn,
        "INSERT INTO blood_requests (hospital_id,blood_group,units_needed,patient_name,urgency) VALUES (%s,%s,%s,%s,%s)",
        (uid, d['blood_group'], d['units_needed'], d.get('patient_name'), d.get('urgency', 'normal')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Request created'}), 201

@app.route('/api/hospital/requests/<int:req_id>', methods=['PUT'])
def update_request(req_id):
    uid, _, e = require_role('hospital')
    if e: return e
    d = request.json
    conn = get_db()
    execute(conn, "UPDATE blood_requests SET status=%s WHERE id=%s AND hospital_id=%s",
            (d['status'], req_id, uid))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Updated'})

# ── hospital inventory ────────────────────────────────────────────────────────

@app.route('/api/hospital/inventory', methods=['GET', 'POST'])
def hospital_inventory():
    uid, _, e = require_role('hospital')
    if e: return e
    conn = get_db()
    if request.method == 'GET':
        data = rows(conn, "SELECT * FROM blood_inventory WHERE hospital_id=%s", (uid,))
        conn.close()
        return jsonify(data)
    d = request.json
    execute(conn,
        "INSERT INTO blood_inventory (hospital_id,blood_group,units_available) VALUES (%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE units_available=%s, updated_at=NOW()",
        (uid, d['blood_group'], d['units_available'], d['units_available']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Inventory updated'})

# ── hospital donations ────────────────────────────────────────────────────────

@app.route('/api/hospital/donations', methods=['GET', 'POST'])
def hospital_donations():
    uid, _, e = require_role('hospital')
    if e: return e
    conn = get_db()
    if request.method == 'GET':
        data = rows(conn,
            "SELECT d.*, dn.name AS donor_name FROM donations d "
            "JOIN donors dn ON d.donor_id=dn.id WHERE d.hospital_id=%s ORDER BY d.donation_date DESC", (uid,))
        conn.close()
        return jsonify(data)
    d = request.json
    donor = row(conn, "SELECT id FROM donors WHERE id=%s", (d['donor_id'],))
    if not donor:
        conn.close()
        return err('Donor not found')
    execute(conn,
        "INSERT INTO donations (donor_id,hospital_id,blood_group,units,donation_date,request_id) VALUES (%s,%s,%s,%s,%s,%s)",
        (d['donor_id'], uid, d['blood_group'], d.get('units', 1), d['donation_date'], d.get('request_id')))
    execute(conn, "UPDATE donors SET last_donation=%s WHERE id=%s", (d['donation_date'], d['donor_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Donation recorded'}), 201

# ── public blood search ───────────────────────────────────────────────────────

@app.route('/api/blood/donors', methods=['GET'])
def search_donors():
    blood = request.args.get('blood_group')
    city  = request.args.get('city')
    state = request.args.get('state')
    sql = "SELECT id,name,blood_group,phone,city,state,last_donation FROM donors WHERE is_available=1"
    params = []
    if blood: sql += " AND blood_group=%s";          params.append(blood)
    if city:  sql += " AND LOWER(city) LIKE %s";     params.append(f'%{city.lower()}%')
    if state: sql += " AND LOWER(state) LIKE %s";    params.append(f'%{state.lower()}%')
    conn = get_db()
    data = rows(conn, sql, params)
    conn.close()
    return jsonify(data)

@app.route('/api/blood/hospitals', methods=['GET'])
def search_hospitals():
    blood = request.args.get('blood_group')
    city  = request.args.get('city')
    state = request.args.get('state')
    sql = ("SELECT h.id,h.name,h.phone,h.city,h.state,h.address,i.units_available "
           "FROM hospitals h JOIN blood_inventory i ON h.id=i.hospital_id WHERE i.units_available>0")
    params = []
    if blood: sql += " AND i.blood_group=%s";        params.append(blood)
    if city:  sql += " AND LOWER(h.city) LIKE %s";   params.append(f'%{city.lower()}%')
    if state: sql += " AND LOWER(h.state) LIKE %s";  params.append(f'%{state.lower()}%')
    conn = get_db()
    data = rows(conn, sql, params)
    conn.close()
    return jsonify(data)

@app.route('/api/blood/requests', methods=['GET'])
def search_requests():
    blood   = request.args.get('blood_group')
    city    = request.args.get('city')
    state   = request.args.get('state')
    urgency = request.args.get('urgency')
    sql = ("SELECT r.*, h.name AS hospital_name, h.city, h.state, h.phone "
           "FROM blood_requests r JOIN hospitals h ON r.hospital_id=h.id WHERE r.status='open'")
    params = []
    if blood:   sql += " AND r.blood_group=%s";      params.append(blood)
    if city:    sql += " AND LOWER(h.city) LIKE %s"; params.append(f'%{city.lower()}%')
    if state:   sql += " AND LOWER(h.state) LIKE %s";params.append(f'%{state.lower()}%')
    if urgency: sql += " AND r.urgency=%s";          params.append(urgency)
    sql += " ORDER BY r.created_at DESC"
    conn = get_db()
    data = rows(conn, sql, params)
    conn.close()
    return jsonify(data)

@app.route('/api/blood/stats', methods=['GET'])
def stats():
    conn = get_db()
    result = {
        'available_donors':    scalar(conn, "SELECT COUNT(*) as c FROM donors WHERE is_available=1"),
        'hospitals':           scalar(conn, "SELECT COUNT(*) as c FROM hospitals"),
        'completed_donations': scalar(conn, "SELECT COUNT(*) as c FROM donations WHERE status='completed'"),
        'open_requests':       scalar(conn, "SELECT COUNT(*) as c FROM blood_requests WHERE status='open'")
    }
    conn.close()
    return jsonify(result)

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("[OK] BloodDrop backend running on http://localhost:5001")
    app.run(debug=True, port=5001)
