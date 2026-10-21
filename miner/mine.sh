#!/bin/sh
# ./mine.sh start [hours]  |  ./mine.sh stop  |  ./mine.sh status
set -eu
cd "$(dirname "$0")"
[ -f .env ] || { echo "copy env-example to .env and set WALLET first"; exit 1; }
case "${1:-status}" in
start)  [ -n "${2:-}" ] && export MINE_HOURS="$2"
        docker compose up -d --build && echo "mining for ${MINE_HOURS:-$(sed -n 's/^MINE_HOURS=//p' .env)} h (0 = until stopped)";;
stop)   docker compose down;;
status) docker compose ps; docker compose logs --tail 8 xmrig 2>/dev/null | grep -E "speed|accepted|new job|block|error|failed" || true;;
*)      echo "usage: ./mine.sh start [hours] | stop | status"; exit 2;;
esac
