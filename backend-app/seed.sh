#!/bin/bash
# Script to seed the database with initial data

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Run the seed script
python -m app.seed

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    echo "Virtual environment deactivated"
fi