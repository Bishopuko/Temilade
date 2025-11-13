-- Create notification_db database for API Gateway
CREATE DATABASE notification_db;

-- Grant privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE notification_db TO postgres;
