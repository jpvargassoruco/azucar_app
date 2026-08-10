-- azucar schema for MySQL (port of backend/app/models/*.py)
-- All datetimes stored as UTC DATETIME. InnoDB + utf8mb4 required (FKs, JSON).

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ai_provider VARCHAR(50) NULL,
    ai_api_key VARCHAR(512) NULL,
    ai_model VARCHAR(100) NULL,
    ai_base_url VARCHAR(255) NULL,
    height INT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS glucose_readings (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    value_mgdl INT NOT NULL,
    `condition` VARCHAR(50) NOT NULL,
    notes VARCHAR(500) NULL,
    PRIMARY KEY (id),
    KEY ix_glucose_user_datetime (user_id, datetime),
    CONSTRAINT fk_glucose_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fasting_sessions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    protocol VARCHAR(50) NOT NULL,
    completed TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY ix_fasting_user (user_id),
    CONSTRAINT fk_fasting_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS habit_logs (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    date DATE NOT NULL,
    habit_key VARCHAR(50) NOT NULL,
    completed TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_date_habit (user_id, date, habit_key),
    CONSTRAINT fk_habit_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alarms (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    type VARCHAR(50) NOT NULL,
    config_time VARCHAR(5) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    KEY ix_alarms_user (user_id),
    CONSTRAINT fk_alarms_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_entries (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    photo_path VARCHAR(500) NULL,
    thumbnail_path VARCHAR(500) NULL,
    notes VARCHAR(1000) NULL,
    ai_analysis JSON NULL,
    PRIMARY KEY (id),
    KEY ix_meals_user_datetime (user_id, datetime),
    CONSTRAINT fk_meals_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_plans (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    preferences VARCHAR(500) NULL,
    plan_data JSON NOT NULL,
    PRIMARY KEY (id),
    KEY ix_meal_plans_user (user_id),
    CONSTRAINT fk_meal_plans_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- endpoint is a URL: ascii charset keeps the 500-char UNIQUE index within limits
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    endpoint VARCHAR(500) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    p256dh VARCHAR(255) NOT NULL,
    auth VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_push_endpoint (endpoint),
    KEY ix_push_user (user_id),
    CONSTRAINT fk_push_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medications (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,
    kind VARCHAR(20) NOT NULL,
    dosage VARCHAR(50) NULL,
    times JSON NOT NULL,
    days_of_week JSON NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    notes VARCHAR(255) NULL,
    PRIMARY KEY (id),
    KEY ix_medications_user (user_id),
    CONSTRAINT fk_medications_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medication_logs (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    medication_id INT UNSIGNED NOT NULL,
    user_id INT UNSIGNED NOT NULL,
    date DATE NOT NULL,
    scheduled_time VARCHAR(5) NOT NULL,
    status VARCHAR(10) NOT NULL,
    marked_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_med_date_time (medication_id, date, scheduled_time),
    KEY ix_med_logs_user (user_id),
    CONSTRAINT fk_med_logs_med FOREIGN KEY (medication_id) REFERENCES medications (id) ON DELETE CASCADE,
    CONSTRAINT fk_med_logs_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS weights (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    weight_kg DOUBLE NOT NULL,
    notes VARCHAR(500) NULL,
    PRIMARY KEY (id),
    KEY ix_weights_user_datetime (user_id, datetime),
    CONSTRAINT fk_weights_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blood_pressures (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    systolic_mmhg INT NOT NULL,
    diastolic_mmhg INT NOT NULL,
    notes VARCHAR(500) NULL,
    PRIMARY KEY (id),
    KEY ix_pressures_user_datetime (user_id, datetime),
    CONSTRAINT fk_pressures_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS hba1c_readings (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    value_percent DOUBLE NOT NULL,
    notes VARCHAR(500) NULL,
    PRIMARY KEY (id),
    KEY ix_hba1c_user_datetime (user_id, datetime),
    CONSTRAINT fk_hba1c_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- New: replaces Redis SETEX dedup keys for reminder sends
CREATE TABLE IF NOT EXISTS sent_notifications (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    dedup_key VARCHAR(120) NOT NULL,
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dedup_key (dedup_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- New: cron watermark enabling the missed-minute catch-up window
CREATE TABLE IF NOT EXISTS cron_state (
    id TINYINT UNSIGNED NOT NULL,
    last_run_utc DATETIME NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO cron_state (id, last_run_utc) VALUES (1, UTC_TIMESTAMP());

SET FOREIGN_KEY_CHECKS = 1;
