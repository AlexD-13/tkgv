-- GestionPlatos — relational schema (draft)
-- Target: SQLite 3 (file-based, no server). Enable foreign keys per connection:
--   PRAGMA foreign_keys = ON;

CREATE TABLE dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    min_quota INTEGER NOT NULL DEFAULT 0,   -- desired threshold (internal control)
    max_quota INTEGER NOT NULL DEFAULT 5,   -- hard limit of registrations
    tested INTEGER NOT NULL DEFAULT 0,      -- internal: dish tried/validated (0/1)
    active INTEGER NOT NULL DEFAULT 1,      -- 0/1
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    client_id TEXT,                         -- device/browser identifier for "already registered" detection
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_reg_dish ON registrations(dish_id);

CREATE TABLE proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dish_name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_prop_status ON proposals(status);

-- Keep updated_at in sync on row update (SQLite has no ON UPDATE).
CREATE TRIGGER dishes_updated_at
AFTER UPDATE ON dishes
FOR EACH ROW
BEGIN
    UPDATE dishes SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- Concurrency (RNF-01): SQLite serializes writes per database file, but
-- concurrent transactions can still raise SQLITE_BUSY. Use a single write
-- transaction (BEGIN IMMEDIATE) and verify
--   (SELECT COUNT(*) FROM registrations WHERE dish_id = ?) < max_quota
-- before inserting into registrations. Set a busy_timeout on the connection.
