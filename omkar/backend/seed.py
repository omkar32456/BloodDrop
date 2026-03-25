import bcrypt
from database import get_db, init_db

init_db()
conn = get_db()
pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()

# Hospitals
conn.executemany(
    "INSERT OR IGNORE INTO hospitals (name,email,password,phone,license_no,address,city,state) VALUES (?,?,?,?,?,?,?,?)",
    [
        ('City General Hospital', 'city@hospital.com',   pw, '9876543210', 'MH-HOSP-001', '123 Main St',  'Mumbai',    'Maharashtra'),
        ('Apollo Blood Bank',     'apollo@hospital.com', pw, '9876543211', 'DL-HOSP-002', '456 Ring Rd',  'Delhi',     'Delhi'),
        ('Care Hospital',         'care@hospital.com',   pw, '9876543212', 'KA-HOSP-003', '789 MG Road',  'Bangalore', 'Karnataka'),
        ('Global Medical Center', 'global@hospital.com', pw, '9876543213', 'TN-HOSP-004', '321 Anna Salai','Chennai',  'Tamil Nadu'),
    ]
)

# Donors
conn.executemany(
    "INSERT OR IGNORE INTO donors (name,email,password,phone,blood_group,city,state,age,weight,is_available) VALUES (?,?,?,?,?,?,?,?,?,?)",
    [
        ('Rahul Sharma', 'rahul@example.com', pw, '9999999991', 'O+',  'Mumbai',    'Maharashtra', 25, 70.0, 1),
        ('Priya Patel',  'priya@example.com', pw, '9999999992', 'A+',  'Delhi',     'Delhi',       28, 58.0, 1),
        ('Amit Singh',   'amit@example.com',  pw, '9999999993', 'B+',  'Bangalore', 'Karnataka',   30, 75.0, 1),
        ('Sneha Rao',    'sneha@example.com', pw, '9999999994', 'AB-', 'Chennai',   'Tamil Nadu',  22, 55.0, 1),
        ('Vikram Nair',  'vikram@example.com',pw, '9999999995', 'O-',  'Mumbai',    'Maharashtra', 35, 80.0, 1),
        ('Anita Desai',  'anita@example.com', pw, '9999999996', 'A-',  'Delhi',     'Delhi',       27, 60.0, 1),
    ]
)
conn.commit()

# Blood inventory per hospital
h_ids = [r[0] for r in conn.execute("SELECT id FROM hospitals ORDER BY id").fetchall()]
blood_groups = ['A+','A-','B+','B-','AB+','AB-','O+','O-']
units = [10, 5, 8, 3, 6, 2, 15, 4]
for hid in h_ids:
    for bg, u in zip(blood_groups, units):
        conn.execute(
            "INSERT OR IGNORE INTO blood_inventory (hospital_id,blood_group,units_available) VALUES (?,?,?)",
            (hid, bg, u)
        )

# Blood requests
conn.executemany(
    "INSERT OR IGNORE INTO blood_requests (hospital_id,blood_group,units_needed,patient_name,urgency,status) VALUES (?,?,?,?,?,?)",
    [
        (h_ids[0], 'O+',  2, 'Patient A', 'urgent',   'open'),
        (h_ids[0], 'AB-', 1, 'Patient B', 'critical', 'open'),
        (h_ids[1], 'B+',  3, 'Patient C', 'normal',   'open'),
        (h_ids[2], 'A+',  2, 'Patient D', 'urgent',   'open'),
        (h_ids[3], 'O-',  1, 'Patient E', 'critical', 'open'),
    ]
)
conn.commit()
conn.close()
print("[OK] Sample data inserted successfully")
print("     Login with any hospital/donor email, password: password123")
