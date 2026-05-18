-- Migration 011: limpieza de filas fantasma en schema_migrations (SPEC-204)
--
-- El INSERT de la migration 005 registraba '003_materialized_views' y
-- '004_aggregates_tables' como migrations aplicadas, pero esos archivos
-- nunca existieron (servian al dashboard, descartado). En los stages donde
-- el 005 ya corrio, esas dos filas quedaron en schema_migrations e inducen
-- a pensar que esas migrations existen.
--
-- El runner (scripts/migrate.py) NO valida checksum al re-aplicar, asi que
-- editar el .sql del 005 solo evita el problema en un fresh apply; esta
-- migration es la que efectivamente borra las filas fantasma de un DB ya
-- migrado. Idempotente: si las filas no estan, el DELETE no hace nada.
DELETE FROM schema_migrations
WHERE version IN ('003_materialized_views', '004_aggregates_tables');
