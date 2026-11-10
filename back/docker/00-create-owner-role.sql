DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'Coffito@admin') THEN
        CREATE ROLE "Coffito@admin";
    END IF;
END
$$;
