DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'Dev@admin') THEN
        CREATE ROLE "Dev@admin";
    END IF;
END
$$;
