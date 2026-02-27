#!/bin/bash
set -a; [ -f ".env" ] && source .env; set +a
exec ./scripts/release/run_go_live_check.sh
