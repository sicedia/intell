-- PostgreSQL initialization script
-- This script runs automatically when the PostgreSQL container starts for the first time
-- The database is already created by POSTGRES_DB, so we just need to set up permissions

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE intell TO intell_user;

-- Connect to the intell database to set up schema permissions
\c intell

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO intell_user;
GRANT CREATE ON SCHEMA public TO intell_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO intell_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO intell_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO intell_user;

