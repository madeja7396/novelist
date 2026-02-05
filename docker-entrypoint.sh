#!/bin/bash
set -e

# Novelist Docker Entrypoint

case "$1" in
  api)
    echo "Starting API server..."
    exec novelist-api
    ;;
  
  agent)
    echo "Starting agent worker..."
    exec novelist-agent
    ;;
  
  python)
    echo "Starting Python legacy mode..."
    cd /app/python
    exec python -m src.cli.main "${@:2}"
    ;;
  
  shell|bash|sh)
    exec /bin/bash
    ;;
  
  *)
    echo "Usage: $0 {api|agent|python|shell}"
    echo ""
    echo "Commands:"
    echo "  api     - Start Go API server"
    echo "  agent   - Start Go agent worker"
    echo "  python  - Run Python CLI (legacy)"
    echo "  shell   - Open shell"
    exit 1
    ;;
esac
