host https://auth-db920.hstgr.io/index.php?db=u805960625_anwari
db name u805960625_anwari
username u805960625_anwari
pass Gmaluka123@


-- Table to store information about Suppliers and Customers
CREATE TABLE party (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE, -- Ensuring party names are unique
    party_type ENUM('Supplier', 'Customer') NOT NULL,
    address TEXT NULL,
    contact_info VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to store details about the items traded (Sheep, Goat)
CREATE TABLE item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE, -- Assuming item names are unique
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to record purchase transactions
CREATE TABLE purchase_transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_date DATE NOT NULL,
    party_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(12, 2) NOT NULL, -- Adjusted precision based on sample data [cite: 7]
    total_amount DECIMAL(15, 2) NOT NULL, -- Adjusted precision based on sample data [cite: 7]
    bill_number VARCHAR(100) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_purchase_party (party_id),
    INDEX idx_purchase_item (item_id),
    INDEX idx_purchase_date (transaction_date),

    FOREIGN KEY (party_id) REFERENCES party(id) ON DELETE RESTRICT, -- Prevent deleting a party if they have transactions
    FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE RESTRICT  -- Prevent deleting an item if it's in transactions
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to record sales transactions
CREATE TABLE sales_transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_date DATE NOT NULL,
    party_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL, -- Live Count [cite: 2, 3]
    weight DECIMAL(10, 2) NULL, -- Weight can be NULL if sale is by quantity only [cite: 2, 3]
    rate DECIMAL(10, 2) NOT NULL, -- Rate per unit (weight or quantity) [cite: 2, 3]
    total_amount DECIMAL(15, 2) NOT NULL, -- Adjusted precision based on sample data [cite: 1, 2, 3]
    bill_number VARCHAR(100) NULL,
    sales_period_start DATE NULL, -- Optional: to match weekly structure [cite: 1, 2, 3]
    sales_period_end DATE NULL,   -- Optional: to match weekly structure [cite: 1, 2, 3]
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_sales_party (party_id),
    INDEX idx_sales_item (item_id),
    INDEX idx_sales_date (transaction_date),

    FOREIGN KEY (party_id) REFERENCES party(id) ON DELETE RESTRICT,
    FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to record payments made or received
CREATE TABLE payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_date DATE NOT NULL,
    party_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL, -- Match precision with transaction amounts
    payment_type ENUM('Paid', 'Received') NOT NULL, -- 'Paid' to suppliers, 'Received' from customers
    reference VARCHAR(255) NULL, -- For bank transaction details, cheque no, etc. [cite: 11]
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_payment_party (party_id),
    INDEX idx_payment_date (payment_date),

    FOREIGN KEY (party_id) REFERENCES party(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert initial items if they are fixed
INSERT INTO item (name, description) VALUES ('Sheep', 'Livestock Sheep');
INSERT INTO item (name, description) VALUES ('Goat', 'Livestock Goat');