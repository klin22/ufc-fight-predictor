-- Run once on an existing PostgreSQL database to preserve missing control times.
-- New databases created from the SQLAlchemy models already allow these NULLs.
BEGIN;
ALTER TABLE fight_stats ALTER COLUMN control_seconds DROP NOT NULL;
ALTER TABLE round_stats ALTER COLUMN control_seconds DROP NOT NULL;
COMMIT;
