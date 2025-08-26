#!/bin/sh
set -e

echo "Running project setup"

echo "Installing Node dependencies"
npm install >/dev/null

echo "Installing Python dependencies"
pip install -r backend/requirements.txt >/dev/null

echo "Setup complete"

