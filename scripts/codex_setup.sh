#!/bin/sh
set -e

echo "Running project setup"

# Install Node.js dependencies
npm install || { echo "npm install failed" >&2; exit 1; }

# Install Python dependencies
pip install -r backend/requirements.txt || { echo "pip install failed" >&2; exit 1; }

