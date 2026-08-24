#!/usr/bin/env bash
# 啟動 webui server（測試埠），驗證 CORS 與 CSRF 防護後關閉。
set -u
cd "$(dirname "$0")/.."

PORT=8899
LOG=/tmp/opencode/webui_server.log
FAIL=0

venv/bin/python cli.py serve --port "$PORT" --no-browser >"$LOG" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null; wait "$SERVER_PID" 2>/dev/null' EXIT

for _ in $(seq 1 30); do
  curl -s "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && break
  sleep 0.3
done

ORIGIN_OK="https://franky5440-afk.github.io"
ORIGIN_BAD="https://evil.example.com"

echo "== 1. 無 Origin 的 GET /api/health =="
curl -si "http://127.0.0.1:$PORT/api/health" | tr -d '\r' | grep -Ei "^HTTP|^access-control|^\{"
echo
echo "== 2. Pages origin 的 GET 應帶 ACAO =="
curl -si -H "Origin: $ORIGIN_OK" "http://127.0.0.1:$PORT/api/health" | tr -d '\r' | grep -Ei "^HTTP|^access-control|^\{"
echo
echo "== 3. 其他 origin 的 GET 不應帶 ACAO =="
OUT=$(curl -si -H "Origin: $ORIGIN_BAD" "http://127.0.0.1:$PORT/api/health" | tr -d '\r')
if echo "$OUT" | grep -qi "access-control-allow-origin"; then
  echo "🔴 FAIL：不該允許的 origin 卻拿到 ACAO"; FAIL=1
else
  echo "$OUT" | grep -Ei "^HTTP|^\{"; echo "✅ 正確：無 ACAO header"
fi
echo
echo "== 4. Pages origin 的 OPTIONS preflight =="
curl -si -X OPTIONS \
  -H "Origin: $ORIGIN_OK" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -H "Access-Control-Request-Private-Network: true" \
  "http://127.0.0.1:$PORT/api/jobs" | tr -d '\r' | grep -Ei "^HTTP|^allow$|^access-control"
echo
echo "== 5. 非 JSON Content-Type 的 POST 仍被拒（CSRF 防護不變）=="
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Origin: $ORIGIN_OK" -F "workflow=video" -F "source=https://example.com/v" \
  "http://127.0.0.1:$PORT/api/jobs"
echo
echo "== 6. 首頁回傳新 UI 且含 title 標記 =="
curl -s "http://127.0.0.1:$PORT/" | grep -c "<title>影片轉錄工具</title>"
curl -s "http://127.0.0.1:$PORT/" | grep -c "view-backend-missing"

echo
if [ "$FAIL" -eq 0 ]; then echo "ALL CHECKS DONE"; else echo "SOME CHECKS FAILED"; fi
exit $FAIL
