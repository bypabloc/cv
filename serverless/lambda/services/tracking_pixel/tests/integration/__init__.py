"""Tests de integracion del Lambda `tracking_pixel` (E2E con moto).

Ejercitan el flujo completo handler -> controller -> service ->
persistencia invocando el `lambda_handler` real con eventos API Gateway
crudos. DynamoDB se emula con `moto` (alta fidelidad, sin AWS real), asi
la suite corre en CI sin red ni credenciales.
"""
