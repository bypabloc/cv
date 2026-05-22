"""Configuracion pytest de los tests de integracion del stream_processor.

Los tests de integracion corren contra recursos AWS reales (Neon
PostgreSQL, DynamoDB Streams). A diferencia del conftest unit, NO mockea
nada: las fixtures preparan y limpian estado real.

Por ahora la suite de integracion esta vacia; este conftest deja el
hook listo para fixtures con cleanup `autouse`.
"""
