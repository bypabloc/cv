#!/usr/bin/env bash
# smoke_test.sh - Smoke test E2E del backend serverless portfolio
#
# Uso:
#   ./scripts/smoke_test.sh [stage]
#   stage: dev (default) | prod
#
# Pre-requisitos:
#   - AWS CLI configurada con profile tfs-dev
#   - jq instalado
#   - curl 8+
#   - DASHBOARD_PASSWORD exportado (si se valida dashboard)
#
# Exit codes:
#   0 - todos los smoke tests pasaron
#   1 - falla critica (endpoint inalcanzable)
#   2 - falla parcial (algun endpoint retorna status inesperado)

set -euo pipefail

STAGE="${1:-dev}"
PROFILE="${AWS_PROFILE:-tfs-dev}"
REGION="us-east-1"
STACK_NAME="portfolio-backend-${STAGE}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

FAILED=0
PASSED=0

log_pass() {
  echo -e "${GREEN}[PASS]${NC} $1"
  PASSED=$((PASSED + 1))
}

log_fail() {
  echo -e "${RED}[FAIL]${NC} $1"
  FAILED=$((FAILED + 1))
}

log_info() {
  echo -e "${YELLOW}[INFO]${NC} $1"
}

# 1. Obtener API endpoint del stack
log_info "Obteniendo ApiEndpoint del stack ${STACK_NAME}..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --profile "$PROFILE" --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text 2>/dev/null || echo "")

if [[ -z "$API_ENDPOINT" ]]; then
  log_fail "No se pudo obtener ApiEndpoint del stack ${STACK_NAME}"
  exit 1
fi

log_info "API Endpoint: ${API_ENDPOINT}"

# 2. Test CORS preflight contra /contact
log_info "Test OPTIONS /contact (CORS preflight)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X OPTIONS "${API_ENDPOINT}/contact" \
  -H "Origin: https://the-full-stack.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type")

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "204" ]]; then
  log_pass "OPTIONS /contact => ${HTTP_CODE}"
else
  log_fail "OPTIONS /contact => ${HTTP_CODE} (esperado 200/204)"
fi

# 3. Test POST /contact sin Turnstile token (espera 400 INVALID_INPUT)
log_info "Test POST /contact sin cf_token (espera 400)..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_ENDPOINT}/contact" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test",
    "email": "smoke@example.com",
    "message": "Smoke test message - ignore"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "400" ]]; then
  log_pass "POST /contact sin token => 400 (validacion correcta)"
else
  log_fail "POST /contact sin token => ${HTTP_CODE} (esperado 400). Body: ${BODY}"
fi

# 4. Test POST /track con session valido (espera 204)
log_info "Test POST /track..."
SESSION_ID="smoke-$(date +%s)-${RANDOM}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${API_ENDPOINT}/track" \
  -H "Content-Type: application/json" \
  -d "{
    \"event_name\": \"page_view\",
    \"page_path\": \"/smoke-test\",
    \"session_id\": \"${SESSION_ID}\"
  }")

if [[ "$HTTP_CODE" == "204" || "$HTTP_CODE" == "200" ]]; then
  log_pass "POST /track => ${HTTP_CODE}"
else
  log_fail "POST /track => ${HTTP_CODE} (esperado 204)"
fi

# 5. Test GET /dashboard/summary sin auth (espera 401)
log_info "Test GET /dashboard/summary sin auth (espera 401)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "${API_ENDPOINT}/dashboard/summary?days=30")

if [[ "$HTTP_CODE" == "401" ]]; then
  log_pass "GET /dashboard sin auth => 401"
else
  log_fail "GET /dashboard sin auth => ${HTTP_CODE} (esperado 401)"
fi

# 6. Test GET /dashboard/summary con auth si DASHBOARD_PASSWORD definido
if [[ -n "${DASHBOARD_PASSWORD:-}" ]]; then
  log_info "Test GET /dashboard/summary con auth..."
  AUTH=$(echo -n "owner:${DASHBOARD_PASSWORD}" | base64)
  RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "${API_ENDPOINT}/dashboard/summary?days=30" \
    -H "Authorization: Basic ${AUTH}")

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [[ "$HTTP_CODE" == "200" ]]; then
    # Validar shape del JSON
    if echo "$BODY" | jq -e '.contacts and .tracking' >/dev/null 2>&1; then
      log_pass "GET /dashboard con auth => 200 + JSON shape OK"
      log_info "Summary: $(echo "$BODY" | jq -c '.')"
    else
      log_fail "GET /dashboard => 200 pero shape invalido: ${BODY}"
    fi
  else
    log_fail "GET /dashboard con auth => ${HTTP_CODE} (esperado 200)"
  fi
else
  log_info "Skip dashboard auth test (DASHBOARD_PASSWORD no definido)"
fi

# 7. Verificar DynamoDB tracking table tiene el event recien insertado
log_info "Esperando 2s para propagacion DynamoDB Stream..."
sleep 2
log_info "Verificando event en DynamoDB tracking-${STAGE}..."

COUNT=$(aws dynamodb scan \
  --profile "$PROFILE" --region "$REGION" \
  --table-name "portfolio-tracking-${STAGE}" \
  --filter-expression "session_id = :sid" \
  --expression-attribute-values "{\":sid\":{\"S\":\"${SESSION_ID}\"}}" \
  --select COUNT \
  --query 'Count' \
  --output text 2>/dev/null || echo "0")

if [[ "$COUNT" -ge 1 ]]; then
  log_pass "DynamoDB tracking-${STAGE} tiene el event de smoke (count=${COUNT})"
else
  log_fail "DynamoDB tracking-${STAGE} NO tiene el event session_id=${SESSION_ID}"
fi

# 8. Verificar SES domain identity
log_info "Verificando SES domain identity..."
SES_FROM=$(aws ssm get-parameter \
  --profile "$PROFILE" --region "$REGION" \
  --name /portfolio/ses-from-address \
  --query 'Parameter.Value' --output text 2>/dev/null || echo "")

if [[ -n "$SES_FROM" ]]; then
  DOMAIN="${SES_FROM##*@}"
  VERIFIED=$(aws sesv2 get-email-identity \
    --profile "$PROFILE" --region "$REGION" \
    --email-identity "$DOMAIN" \
    --query 'VerifiedForSendingStatus' \
    --output text 2>/dev/null || echo "false")

  if [[ "$VERIFIED" == "True" || "$VERIFIED" == "true" ]]; then
    log_pass "SES domain ${DOMAIN} verificado"
  else
    log_fail "SES domain ${DOMAIN} NO verificado (VerifiedForSending=${VERIFIED})"
  fi
else
  log_info "Skip SES check (SSM /portfolio/ses-from-address no encontrado)"
fi

# Resumen final
echo ""
echo "================================================================"
echo " Smoke test summary (stage: ${STAGE})"
echo "================================================================"
echo -e " ${GREEN}Passed:${NC} ${PASSED}"
echo -e " ${RED}Failed:${NC} ${FAILED}"
echo "================================================================"

if [[ "$FAILED" -eq 0 ]]; then
  echo -e "${GREEN}All smoke tests PASSED${NC}"
  exit 0
else
  echo -e "${RED}Some smoke tests FAILED${NC}"
  exit 2
fi
