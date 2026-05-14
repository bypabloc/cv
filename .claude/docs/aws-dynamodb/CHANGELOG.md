# CHANGELOG - AWS DynamoDB Knowledge Base

> Historial de decisiones y arqueologia del diseño.

## 2026-05-13: Initial Research + Documentation

### Decisiones Tomadas

1. **On-Demand Capacity Mode (OBLIGATORIO)**
   - Razon: Volumen bajo (50-200 contacts/mes, 5-15K tracking/mes), impredecible
   - Costo: <$0.01/mes vs mínimo $1.16/mes en Provisioned
   - AWS official recommendation post-Nov 2024: On-Demand por default
   - Ref: [AWS DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)

2. **Dos Tablas Separadas (NO Single-Table Design)**
   - Razon: Dominio desacoplado (contacts vs tracking), queries independientes
   - Single-table design descartado: complejidad no justificada para este scope
   - Futuro: Revisitin Q3 2026 si dashboard integrado requiere.
   - Ref: [Rick Houlihan - Single-Table Design](https://www.pluralsight.com/resources/webinars/nosql-for-grownups-dynamodb-single-table-modeling-with-rick-houl)

3. **TTL para Tracking (60 dias retencion)**
   - Razon: Borra items automaticamente sin costo (no consume WCU), simplifica operaciones
   - Implementacion: `expires_at` (Number, Unix epoch seconds), Enabled=true en SAM
   - Ahorro: ~100% en storage cost post-60d
   - Ref: [AWS DynamoDB TTL Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)

4. **Zero GSI (Por Ahora)**
   - Razon: Partition key + sort key cubren queries actuales
   - Tabla contacts: get_item(id), list by date → sort key opcional, no GSI
   - Tabla tracking: query(session_id), get events → sort key `page_id` existente
   - GSI cuesto 2x write cost → no vale para este volumen
   - Futuro: Agregar GSI(email) en contacts si anti-spam requiere busqueda frecuente
   - Ref: [DynamoDB Global Secondary Index Patterns](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)

5. **Python 3.13 + boto3 (Resource API)**
   - Razon: Lambda runtime standard, boto3 Resource API mas Pythonic
   - Type hints obligatorios (Decimal para numeros)
   - Validacion de input en Lambda (jsonschema)
   - Ref: [boto3 DynamoDB Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html)

6. **AWS SAM para IaC**
   - Razon: Infraestructura as code, reproducible, git-tracked
   - Template YAML define tablas, Lambda functions, IAM roles, PITR
   - Deployment via `sam deploy --guided` o CI/CD
   - Ref: [AWS Serverless Application Model](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)

7. **IAM Least Privilege (OBLIGATORIO)**
   - Contact form: solo `dynamodb:PutItem` en contacts
   - Tracking pixel: solo `dynamodb:PutItem` en tracking
   - Admin dashboard (futuro): `Query` + `GetItem` readonly
   - NUNCA wildcard `dynamodb:*`
   - Ref: [AWS IAM Best Practices for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/using-identity-based-policies.html)

8. **Encryption by Default (AWS-owned Keys)**
   - Razon: DynamoDB encripta at rest por default, sin costo adicional
   - Customer-managed KMS opcional si compliance requiere (cuesta $1/mes + requests)
   - In-transit: HTTPS obligatorio (AWS internal, no exposicion)
   - Ref: [DynamoDB Encryption at Rest](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/encryption.howitworks.html)

9. **PITR Enabled (Optional Pero Recomendado)**
   - Razon: Recuperacion ante borrados accidentales, costo bajo ($0.20/GB/mes)
   - 35 dias retencion
   - No incluye TTL deletes
   - Ref: [DynamoDB Point-in-Time Recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery.html)

### Pricing Verified

- **us-east-1 On-Demand (Mayo 2026):**
  - Write: $1.25 / 1M RU
  - Read: $0.25 / 1M RU
  - Storage: $0.25 / GB-month
  - Free tier: 25GB storage + 25WCU + 25RCU (provisioned) O 200M requests (on-demand)

- **Estimacion Portfolio:**
  - Contacts: ~$0.0004/mes
  - Tracking: ~$0.0057/mes
  - **Total: <$0.01/mes** ✅

### Anti-Patterns Identificados

- ❌ DynamoDB directo desde browser (security risk)
- ❌ Hardcodear table names en codigo
- ❌ Sin input validation (injection risk)
- ❌ Scan sin filter (costoso)
- ❌ Single-table design forzado cuando dos tablas claras

### Fuentes Utilizadas

1. [AWS DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
2. [boto3 DynamoDB Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html)
3. [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
4. [DynamoDB Pricing & Cost Calculator](https://aws.amazon.com/dynamodb/pricing/)
5. [Rick Houlihan - DynamoDB Single-Table Design (Pluralsight)](https://www.pluralsight.com/resources/webinars/nosql-for-grownups-dynamodb-single-table-modeling-with-rick-houl)
6. [Alex DeBrie - The What, Why, and When of Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)

### Documentos Generados

1. `README.md` — Indice navegable Knowledge Tree
2. `01-architecture.md` — Modelo NoSQL key-value, tablas, items, atributos
3. `02-capacity-modes.md` — On-Demand vs Provisioned (DECISIVO)
4. `03-single-table-design.md` — Patron avanzado (NO aplicado)
5. `04-ttl-tracking.md` — TTL 60 dias para tabla tracking
6. `05-gsi-patterns.md` — GSI patterns (DESCARTADO por ahora)
7. `06-boto3-python.md` — Codificacion Lambda handlers
8. `07-deployment-sam.md` — SAM template completo + deploy steps
9. `08-cost-optimization.md` — Pricing breakdown, estimaciones, free tier
10. `09-security-best-practices.md` — IAM least privilege, encryption, compliance

### Knowledge Tree Activado

- Patrón del referente: `docs/progress/explore_cloudflare-pages-deployment.md`
- Estructura: README.md (index) + 9 capitulos modulares
- Idioma: Español, terminos tecnicos en ingles
- Sin atribucion de IA
- Verificado: 2026-05-13

### Siguiente Fase

- Q2 2026: Implementar SAM template en CI/CD (GitHub Actions)
- Q3 2026: Evaluar dashboard si requiere GSI o caching
- Q4 2026: Migracion a Provisioned si volumen sostenido >10K items/mes
- 2027: Evaluar DynamoDB Global Tables si internacionalizacion requiere

---

**Documentacion completa:** [README.md](README.md)
