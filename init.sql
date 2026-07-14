CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    date_posted VARCHAR(100),
    job_link VARCHAR(2048) UNIQUE NOT NULL,
    description TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS people (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    headline TEXT,
    location VARCHAR(255),
    profile_link VARCHAR(2048) UNIQUE NOT NULL,
    snippet TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
