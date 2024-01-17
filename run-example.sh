#!/bin/bash

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# For python virtual environment
source "$DIR"/../get-score-venv/bin/activate

# Run the main.py
python "$DIR"/main.py -u studentID -p password -n name \
    -y 2023-2024 -s 1 \
    -w webhookURL
