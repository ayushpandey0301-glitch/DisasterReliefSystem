    CREATE DATABASE IF NOT EXISTS disaster_relief_db;

    USE disaster_relief_db;


    -- =========================================
    -- 1. USERS TABLE
    -- =========================================

    CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'coordinator', 'volunteer') NOT NULL DEFAULT 'volunteer',
        phone VARCHAR(20),
        status ENUM('active', 'inactive') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    -- =========================================
    -- 2. DISASTERS TABLE
    -- =========================================

    CREATE TABLE disasters (
        disaster_id INT AUTO_INCREMENT PRIMARY KEY,
        disaster_name VARCHAR(150) NOT NULL,
        disaster_type ENUM(
            'Flood',
            'Earthquake',
            'Cyclone',
            'Landslide',
            'Fire',
            'Drought',
            'Other'
        ) NOT NULL,
        description TEXT,
        location VARCHAR(255) NOT NULL,
        severity ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        status ENUM('Active', 'Resolved', 'Closed') DEFAULT 'Active',
        created_by INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (created_by)
            REFERENCES users(user_id)
            ON DELETE SET NULL
    );


    -- =========================================
    -- 3. RESOURCES TABLE
    -- =========================================

    CREATE TABLE resources (
        resource_id INT AUTO_INCREMENT PRIMARY KEY,
        resource_name VARCHAR(150) NOT NULL,
        resource_type ENUM(
            'Food',
            'Water',
            'Medicine',
            'Clothing',
            'Shelter Equipment',
            'Emergency Equipment',
            'Other'
        ) NOT NULL,
        quantity INT NOT NULL DEFAULT 0,
        unit VARCHAR(50) NOT NULL,
        location VARCHAR(255) NOT NULL,
        minimum_stock INT DEFAULT 0,
        expiry_date DATE,
        status ENUM('Available', 'Low Stock', 'Out of Stock') DEFAULT 'Available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    -- =========================================
    -- 4. RESOURCE REQUESTS TABLE
    -- =========================================

    CREATE TABLE resource_requests (
        request_id INT AUTO_INCREMENT PRIMARY KEY,
        disaster_id INT NOT NULL,
        requested_by INT NOT NULL,
        resource_type VARCHAR(100) NOT NULL,
        resource_name VARCHAR(150) NOT NULL,
        quantity_requested INT NOT NULL,
        priority ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
        request_location VARCHAR(255) NOT NULL,
        reason TEXT,
        status ENUM(
            'Pending',
            'Approved',
            'Rejected',
            'Partially Allocated',
            'Completed'
        ) DEFAULT 'Pending',
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (disaster_id)
            REFERENCES disasters(disaster_id)
            ON DELETE CASCADE,

        FOREIGN KEY (requested_by)
            REFERENCES users(user_id)
            ON DELETE CASCADE
    );


    -- =========================================
    -- 5. RESOURCE ALLOCATIONS TABLE
    -- =========================================

    CREATE TABLE resource_allocations (
        allocation_id INT AUTO_INCREMENT PRIMARY KEY,
        request_id INT NOT NULL,
        resource_id INT NOT NULL,
        allocated_quantity INT NOT NULL,
        allocated_by INT NOT NULL,
        allocation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('Allocated', 'In Transit', 'Delivered', 'Cancelled')
            DEFAULT 'Allocated',

        FOREIGN KEY (request_id)
            REFERENCES resource_requests(request_id)
            ON DELETE CASCADE,

        FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON DELETE CASCADE,

        FOREIGN KEY (allocated_by)
            REFERENCES users(user_id)
            ON DELETE CASCADE
    );


    -- =========================================
    -- 6. SHELTERS TABLE
    -- =========================================

    CREATE TABLE shelters (
        shelter_id INT AUTO_INCREMENT PRIMARY KEY,
        shelter_name VARCHAR(150) NOT NULL,
        location VARCHAR(255) NOT NULL,
        capacity INT NOT NULL,
        current_occupancy INT DEFAULT 0,
        contact_number VARCHAR(20),
        facilities TEXT,
        status ENUM('Available', 'Full', 'Closed') DEFAULT 'Available',
        disaster_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (disaster_id)
            REFERENCES disasters(disaster_id)
            ON DELETE SET NULL
    );


    -- =========================================
    -- 7. VOLUNTEERS TABLE
    -- =========================================

    CREATE TABLE volunteers (
        volunteer_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL UNIQUE,
        skills VARCHAR(255),
        availability ENUM('Available', 'Busy', 'Unavailable')
            DEFAULT 'Available',
        emergency_contact VARCHAR(20),
        address VARCHAR(255),
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
    );


    -- =========================================
    -- 8. VEHICLES TABLE
    -- =========================================

    CREATE TABLE vehicles (
        vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
        vehicle_number VARCHAR(50) NOT NULL UNIQUE,
        vehicle_type ENUM(
            'Ambulance',
            'Truck',
            'Van',
            'Rescue Vehicle',
            'Other'
        ) NOT NULL,
        capacity VARCHAR(100),
        driver_name VARCHAR(100),
        driver_contact VARCHAR(20),
        location VARCHAR(255),
        status ENUM(
            'Available',
            'In Use',
            'Maintenance'
        ) DEFAULT 'Available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    -- =========================================
    -- 9. TASKS TABLE
    -- =========================================

    CREATE TABLE tasks (
        task_id INT AUTO_INCREMENT PRIMARY KEY,
        volunteer_id INT NOT NULL,
        disaster_id INT NOT NULL,
        task_title VARCHAR(150) NOT NULL,
        task_description TEXT,
        location VARCHAR(255) NOT NULL,
        assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        status ENUM(
            'Assigned',
            'In Progress',
            'Completed',
            'Cancelled'
        ) DEFAULT 'Assigned',

        FOREIGN KEY (volunteer_id)
            REFERENCES volunteers(volunteer_id)
            ON DELETE CASCADE,

        FOREIGN KEY (disaster_id)
            REFERENCES disasters(disaster_id)
            ON DELETE CASCADE
    );


    -- =========================================
    -- 10. ACTIVITY LOGS TABLE
    -- =========================================

    CREATE TABLE activity_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        action VARCHAR(255) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE SET NULL
    );