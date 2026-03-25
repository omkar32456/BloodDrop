-- BloodDrop Database Schema
-- Import this file in phpMyAdmin: Database > Import > Select this file

CREATE DATABASE IF NOT EXISTS blooddrop;
USE blooddrop;

-- ── DONORS ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS donors (
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
);

-- ── HOSPITALS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hospitals (
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
);

-- ── BLOOD INVENTORY ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS blood_inventory (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id     INT NOT NULL,
    blood_group     VARCHAR(5) NOT NULL,
    units_available INT DEFAULT 0,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_hosp_blood (hospital_id, blood_group),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ── BLOOD REQUESTS ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS blood_requests (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id  INT NOT NULL,
    blood_group  VARCHAR(5) NOT NULL,
    units_needed INT NOT NULL,
    patient_name VARCHAR(100),
    urgency      ENUM('normal','urgent','critical') DEFAULT 'normal',
    status       ENUM('open','fulfilled','closed') DEFAULT 'open',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ── DONATIONS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS donations (
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
);


