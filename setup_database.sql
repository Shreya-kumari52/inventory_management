-- Create database
CREATE DATABASE IF NOT EXISTS inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inventory_db;

-- Drop tables if they exist (for fresh setup)
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items table
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category ENUM('Paint', 'Hardware') NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    purchase_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    quality VARCHAR(50) NOT NULL,
    image VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_name (name),
    INDEX idx_created_at (created_at)
);

-- Insert default owner account
-- Email: owner@shop.com
-- Password: admin123 (bcrypt hashed)
INSERT INTO users (email, password) VALUES 
('owner@shop.com', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi');

-- Sample data
INSERT INTO items (name, category, quantity, purchase_price, selling_price, quality, image) VALUES
('Asian Paints Royale', 'Paint', 50, 250.00, 350.00, 'Excellent', NULL),
('Nerolac Premium', 'Paint', 30, 220.00, 320.00, 'Good', NULL),
('Hammer Drill', 'Hardware', 10, 1500.00, 2200.00, 'Excellent', NULL),
('Screwdriver Set', 'Hardware', 25, 250.00, 450.00, 'Good', NULL);