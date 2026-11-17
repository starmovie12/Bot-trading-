#!/usr/bin/env bash
# tools/clock.sh (MISSION V19): IST and UTC now.
echo "IST $(TZ=Asia/Kolkata date "+%Y-%m-%d %H:%M:%S") | UTC $(date -u "+%Y-%m-%dT%H:%M:%SZ")"
