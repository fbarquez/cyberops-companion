-- IR Companion Database Initialization Script
-- This script runs automatically when the PostgreSQL container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ir_companion;

-- Set search path
SET search_path TO ir_companion, public;

-- Grant permissions (for the application user)
GRANT ALL PRIVILEGES ON SCHEMA ir_companion TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ir_companion TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ir_companion TO postgres;

-- Create audit log function for evidence chain integrity
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to generate hash for evidence chain
CREATE OR REPLACE FUNCTION generate_evidence_hash(
    p_content TEXT,
    p_previous_hash TEXT DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    v_data TEXT;
BEGIN
    IF p_previous_hash IS NULL THEN
        v_data := p_content;
    ELSE
        v_data := p_content || p_previous_hash;
    END IF;
    RETURN encode(digest(v_data, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'IR Companion database initialized successfully at %', NOW();
END $$;
