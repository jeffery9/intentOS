#!/bin/bash
# IntentOS 健康检查与自愈脚本
# 用法：./scripts/auto-heal.sh

set -e

INTENTOS_URL="${INTENTOS_URL:-http://localhost:8080}"
INTENTOS_API_TOKEN="${INTENTOS_API_TOKEN:-intentos-secret-token}"
HEALTH_ENDPOINT="/v1/status"
MAX_RETRIES=5
RETRY_DELAY=10
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_health() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 5 \
        -H "Authorization: Bearer ${INTENTOS_API_TOKEN}" \
        "${INTENTOS_URL}${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")
    if [ "$response" -eq 200 ]; then
        return 0
    else
        return 1
    fi
}

send_alert() {
    local message="$1"
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 IntentOS Alert: $message\"}" \
            >/dev/null 2>&1 || true
    fi
    log "🚨 ALERT: $message"
}

restart_service() {
    log "⚠️  Health check failed! Attempting restart..."
    
    # systemd
    if command -v systemctl &> /dev/null && systemctl is-active --quiet intentos 2>/dev/null; then
        log "🔄 Restarting via systemd..."
        sudo systemctl restart intentos
    # Docker
    elif command -v docker &> /dev/null && docker ps -q -f name=intentos-main | grep -q .; then
        log "🔄 Restarting via Docker..."
        docker restart intentos-main
    # Kubernetes
    elif command -v kubectl &> /dev/null && kubectl get deployment intentos &>/dev/null; then
        log "🔄 Restarting via Kubernetes..."
        kubectl rollout restart deployment/intentos
    else
        log "⚠️  No supported service manager found!"
        return 1
    fi
    
    log "⏳ Waiting ${RETRY_DELAY}s for service to recover..."
    sleep $RETRY_DELAY
}

# 主循环
log "🏥 IntentOS Health Watchdog started"
log "📍 Monitoring: ${INTENTOS_URL}${HEALTH_ENDPOINT}"
log "📊 Check interval: 60s"
log ""

retry_count=0
consecutive_failures=0

while true; do
    if ! check_health; then
        consecutive_failures=$((consecutive_failures + 1))
        log "❌ Health check failed (consecutive: $consecutive_failures)"
        
        if [ $consecutive_failures -ge 3 ]; then
            retry_count=$((retry_count + 1))
            log "⚠️  Attempting restart ($retry_count/$MAX_RETRIES)"
            
            if restart_service; then
                if check_health; then
                    log "✅ Service recovered!"
                    consecutive_failures=0
                    retry_count=0
                else
                    log "❌ Restart failed, service still unhealthy"
                fi
            fi
            
            if [ $retry_count -ge $MAX_RETRIES ]; then
                send_alert "IntentOS health check failed after $MAX_RETRIES restart attempts"
                retry_count=0
            fi
        fi
    else
        if [ $consecutive_failures -gt 0 ]; then
            log "✅ Service recovered after $consecutive_failures failures"
        fi
        consecutive_failures=0
    fi
    
    sleep 60
done
