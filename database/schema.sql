CREATE DATABASE IF NOT EXISTS shulebora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shulebora_db;

CREATE TABLE IF NOT EXISTS users(
 id INT AUTO_INCREMENT PRIMARY KEY, full_name VARCHAR(150) NOT NULL, email VARCHAR(190) UNIQUE NOT NULL,
 phone VARCHAR(40) DEFAULT '', password_hash VARCHAR(255) NOT NULL,
 role ENUM('SUPERADMIN','ADMIN','MEMBER') DEFAULT 'MEMBER',
 status ENUM('ACTIVE','BLOCKED') DEFAULT 'ACTIVE',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS schools(
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200) NOT NULL, location VARCHAR(200) DEFAULT '',
 school_type VARCHAR(100) DEFAULT '', description TEXT, phone VARCHAR(40) DEFAULT '', email VARCHAR(190) DEFAULT '',
 website VARCHAR(255) DEFAULT '', address VARCHAR(255) DEFAULT '', logo VARCHAR(255) DEFAULT NULL,
 publication_status ENUM('PUBLISHED','PENDING','UNPUBLISHED') DEFAULT 'PENDING', rating DECIMAL(3,2) DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_status(publication_status), INDEX idx_location(location)
);
CREATE TABLE IF NOT EXISTS school_images(
 id INT AUTO_INCREMENT PRIMARY KEY, school_id INT NOT NULL, title VARCHAR(200) DEFAULT '',
 image_path VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS activities(
 id INT AUTO_INCREMENT PRIMARY KEY, school_id INT NOT NULL, title VARCHAR(200) NOT NULL,
 category VARCHAR(100) DEFAULT '', description TEXT, activity_date DATE NULL, image VARCHAR(255) DEFAULT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS features(
 id INT AUTO_INCREMENT PRIMARY KEY, school_id INT NOT NULL, name VARCHAR(200) NOT NULL, description TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS facilities(
 id INT AUTO_INCREMENT PRIMARY KEY, school_id INT NOT NULL, name VARCHAR(200) NOT NULL, description TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS qualifications(
 id INT AUTO_INCREMENT PRIMARY KEY, school_id INT NOT NULL, name VARCHAR(200) NOT NULL, description TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS school_contacts(
 id INT AUTO_INCREMENT PRIMARY KEY, school_id INT NOT NULL, contact_type VARCHAR(50) DEFAULT 'GENERAL',
 label VARCHAR(100) DEFAULT '', value VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS likes(
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, school_id INT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_like(user_id,school_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS contact_messages(
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(150) NOT NULL, email VARCHAR(190) NOT NULL,
 subject VARCHAR(255) NOT NULL, message TEXT NOT NULL, status ENUM('NEW','READ','REPLIED') DEFAULT 'NEW',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS school_admins(
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, school_id INT NOT NULL,
 UNIQUE KEY uq_admin_school(user_id,school_id),
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
);

INSERT INTO schools(name,location,school_type,description,publication_status)
SELECT 'NIA Academy','Zanzibar','International School','A modern school focused on academic excellence, discipline and innovation.','PUBLISHED'
WHERE NOT EXISTS(SELECT 1 FROM schools WHERE name='NIA Academy');
INSERT INTO schools(name,location,school_type,description,publication_status)
SELECT 'Zanzibar Modern School','Urban West','Secondary School','Quality education and student development in Zanzibar.','PUBLISHED'
WHERE NOT EXISTS(SELECT 1 FROM schools WHERE name='Zanzibar Modern School');
INSERT INTO schools(name,location,school_type,description,publication_status)
SELECT 'Al-Noor Islamic School','Kisauni','Primary School','Education combining academic learning and character development.','PENDING'
WHERE NOT EXISTS(SELECT 1 FROM schools WHERE name='Al-Noor Islamic School');
