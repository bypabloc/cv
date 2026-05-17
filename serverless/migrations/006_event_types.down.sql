-- Rollback 006: elimina la tabla catalogo event_types.
-- Debe correr DESPUES del rollback de 007 (que tiene la FK a esta tabla);
-- el runner aplica los .down.sql en orden inverso, asi que 007 ya se revirtio.

BEGIN;

DROP TABLE IF EXISTS event_types;

COMMIT;
