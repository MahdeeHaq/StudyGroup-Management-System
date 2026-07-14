-- ============================================================
-- Study Group Management System
-- Database Schema (MySQL)
-- Course: CSE-224 Database Management System Lab
-- ============================================================

DROP DATABASE IF EXISTS study_group_db;
CREATE DATABASE study_group_db;
USE study_group_db;

-- ------------------------------------------------------------
-- Table: subjects
-- ------------------------------------------------------------
CREATE TABLE subjects (
    subject_id   INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(20)  NOT NULL UNIQUE,
    subject_name VARCHAR(100) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: members
-- ------------------------------------------------------------
CREATE TABLE members (
    member_id   INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    phone       VARCHAR(20),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: study_groups
-- One-to-many from subjects and members (organizer)
-- max_members enables a simple capacity rule enforced by the app
-- ------------------------------------------------------------
CREATE TABLE study_groups (
    group_id      INT AUTO_INCREMENT PRIMARY KEY,
    group_name    VARCHAR(150) NOT NULL,
    subject_id    INT NOT NULL,
    organizer_id  INT NOT NULL,
    meeting_time  DATETIME NOT NULL,
    location      VARCHAR(150) NOT NULL,
    description   VARCHAR(255),
    max_members   INT NOT NULL DEFAULT 8,
    status        ENUM('Scheduled','Ongoing','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_group_subject
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_group_organizer
        FOREIGN KEY (organizer_id) REFERENCES members(member_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------
-- Table: group_members  (junction / bridge table)
-- Many-to-many: a member can join many groups, a group has many members
-- ------------------------------------------------------------
CREATE TABLE group_members (
    group_id  INT NOT NULL,
    member_id INT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, member_id),
    CONSTRAINT fk_gm_group
        FOREIGN KEY (group_id) REFERENCES study_groups(group_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gm_member
        FOREIGN KEY (member_id) REFERENCES members(member_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ------------------------------------------------------------
-- Table: materials
-- Files (notes, slides, PDFs) attached to a study group.
-- One-to-many from study_groups and members (uploader)
-- ------------------------------------------------------------
CREATE TABLE materials (
    material_id        INT AUTO_INCREMENT PRIMARY KEY,
    group_id            INT NOT NULL,
    uploaded_by          INT NOT NULL,
    original_filename    VARCHAR(255) NOT NULL,
    stored_filename       VARCHAR(255) NOT NULL,
    description          VARCHAR(255),
    uploaded_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_material_group
        FOREIGN KEY (group_id) REFERENCES study_groups(group_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_material_member
        FOREIGN KEY (uploaded_by) REFERENCES members(member_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------
-- Table: admins
-- Gates create/edit/delete access to subjects, members, and
-- study groups. Password hashes are inserted by the Flask app
-- on first run (see ensure_default_admin() in app.py), never
-- stored in plain text here.
-- ------------------------------------------------------------
CREATE TABLE admins (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Sample data
-- ============================================================

INSERT INTO subjects (subject_code, subject_name) VALUES
('CSE-224', 'Database Management System'),
('CSE-215', 'Data Structures'),
('CSE-311', 'Computer Networks'),
('MAT-201', 'Discrete Mathematics');

INSERT INTO members (full_name, email, phone) VALUES
('Mahdee Haque', 'mahdee.haque@example.com', '01711111111'),
('Nusrat Jahan', 'nusrat.jahan@example.com', '01722222222'),
('Rifat Karim', 'rifat.karim@example.com', '01733333333'),
('Farzana Akter', 'farzana.akter@example.com', '01744444444'),
('Tanvir Ahmed', 'tanvir.ahmed@example.com', '01755555555');

-- meeting_time values are set relative-looking dates; feel free to
-- edit these in phpMyAdmin so a couple fall within the next 7 days
-- to see the "This week" badge in the UI.
INSERT INTO study_groups (group_name, subject_id, organizer_id, meeting_time, location, description, max_members, status) VALUES
('DBMS Lab Revision', 1, 1, '2026-07-10 17:00:00', 'Library Room 3', 'Reviewing SQL joins and normalization before the lab exam.', 6, 'Scheduled'),
('Data Structures Sprint', 2, 2, '2026-07-08 15:30:00', 'CSE Building, Room 210', 'Practicing tree and graph problems.', 5, 'Scheduled'),
('Networking Concepts', 3, 3, '2026-07-05 18:00:00', 'Online (Google Meet)', 'Covered OSI model and subnetting basics.', 8, 'Completed');

INSERT INTO group_members (group_id, member_id) VALUES
(1, 1), (1, 2), (1, 4),
(2, 2), (2, 3), (2, 5),
(3, 3), (3, 4), (3, 5);

-- No admin row here on purpose — app.py creates a default
-- admin (username: admin / password: admin123) the first time
-- it runs against an empty admins table.
