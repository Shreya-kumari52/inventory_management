-- 1. Database create
CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

-- 2. OLD TABLES DELETE
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS items;

-- 3. USERS TABLE
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(100)
);

-- 4. MULTI USERS (FINAL)
INSERT INTO users (username, password)
VALUES 
('deepak', 'deepak123'),
('raushan', 'raushan123'),
('naman', 'naman123');

-- 5. ITEMS TABLE (optimized)
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    weight VARCHAR(50),
    purchase_price FLOAT,
    selling_price FLOAT,
    quality VARCHAR(50),
    image VARCHAR(255)
);

-- 6. 🔥 SEARCH SPEED FAST (INDEX)
CREATE INDEX idx_name ON items(name);
CREATE INDEX idx_category ON items(category);