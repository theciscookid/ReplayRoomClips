#!/bin/bash
echo "[-] Stopping any existing server on port 8000..."
fuser -k 8000/tcp 2>/dev/null
echo "[-] Activating virtual environment..."
source venv/bin/activate
echo "[+] Starting Self-Evolving Console..."
uvicorn main:app --reload --port 8000
