#!/bin/bash

# Streamlit needs "studio/.." as Python path to find our module files
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export PYTHONPATH="$DIR/.."

streamlit run ./studio_app.py