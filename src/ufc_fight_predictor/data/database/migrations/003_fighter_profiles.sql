-- Add fighter profile columns to an existing database; new databases get them from the models.
BEGIN;
ALTER TABLE fighters
    ADD COLUMN IF NOT EXISTS height_in INTEGER,
    ADD COLUMN IF NOT EXISTS reach_in INTEGER,
    ADD COLUMN IF NOT EXISTS stance VARCHAR,
    ADD COLUMN IF NOT EXISTS dob DATE;
COMMIT;
