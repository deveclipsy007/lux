#!/bin/sh
set -e

echo "Running project setup"

# Install project dependencies
npm install
pip install -r backend/requirements.txt
npx playwright install

