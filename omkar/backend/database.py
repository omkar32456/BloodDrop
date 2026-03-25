import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'blooddrop'
}

def get_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def init_db():
    conn = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS blooddrop")
    cursor.execute("USE blooddrop")
    cursor.executemany("", [])

    statements = [
        """CREATE TABLE IF NOT EXISTS donors (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            name          VARCHAR(100) NOT NULL,
            email         VARCHAR(100) UNIQUE NOT NULL,
            password      VARCHAR(255) NOT NULL,
            phone         VARCHAR(20),
            blood_group   VARCHAR(5) NOT NULL,
            city          VARCHAR(100),
            state         VARCHAR(100),
            age           INT,
            weight        FLOAT,
            is_available  TINYINT(1) DEFAULT 1,
            last_donation DATE,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS hospitals (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(150) NOT NULL,
            email       VARCHAR(100) UNIQUE NOT NULL,
            password    VARCHAR(255) NOT NULL,
            phone       VARCHAR(20),
            license_no  VARCHAR(50) UNIQUE NOT NULL,
            address     VARCHAR(255),
            city        VARCHAR(100) NOT NULL,
            state       VARCHAR(100) NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS blood_inventory (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            hospital_id     INT NOT NULL,
            blood_group     VARCHAR(5) NOT NULL,
            units_available INT DEFAULT 0,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_hosp_blood (hospital_id, blood_group),
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS blood_requests (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            hospital_id  INT NOT NULL,
            blood_group  VARCHAR(5) NOT NULL,
            units_needed INT NOT NULL,
            patient_name VARCHAR(100),
            urgency      ENUM('normal','urgent','critical') DEFAULT 'normal',
            status       ENUM('open','fulfilled','closed') DEFAULT 'open',
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS donations (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            donor_id      INT NOT NULL,
            hospital_id   INT NOT NULL,
            blood_group   VARCHAR(5) NOT NULL,
            units         INT DEFAULT 1,
            donation_date DATE NOT NULL,
            status        ENUM('scheduled','completed','cancelled') DEFAULT 'completed',
            request_id    INT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id)    REFERENCES donors(id) ON DELETE CASCADE,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
            FOREIGN KEY (request_id)  REFERENCES blood_requests(id) ON DELETE SET NULL
        )"""
    ]
    for s in statements:
        cursor.execute(s)
    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] MySQL Database ready: blooddrop")
