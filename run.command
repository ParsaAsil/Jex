#!/bin/bash
cd "$(dirname "$0")"

echo "Setting up jex..."

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install the package
pip install -e ".[clipboard]" --quiet 2>&1 | tail -1

echo "Launching jex with sample.json..."
echo ""

# Run jex with the sample file
python -m jex.cli sample.json
