-- GestionPlatos — relational schema (draft)
-- Target: MySQL 8 (InnoDB, utf8mb4). Types chosen to stay SQLite-compatible for local dev.

CREATE TABLE dishes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    min_quota INT NOT NULL DEFAULT 0,        -- desired threshold (internal control)
    max_quota INT NOT NULL DEFAULT 5,        -- hard limit of registrations
    tested TINYINT(1) NOT NULL DEFAULT 0,   -- internal: dish tried/validated
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE registrations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dish_id BIGINT UNSIGNED NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    client_id VARCHAR(64) NULL,             -- device/browser identifier for "already registered" detection
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reg_dish FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    INDEX idx_reg_dish (dish_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE proposals (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    dish_name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prop_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Concurrency (RNF-01): when registering, lock the dish row and verify
-- (SELECT COUNT(*) FROM registrations WHERE dish_id = ?) < max_quota
-- before inserting into registrations. Use SELECT ... FOR UPDATE or a
-- conditional UPDATE with affected-rows check.
