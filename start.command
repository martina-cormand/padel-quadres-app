#!/bin/bash
cd "$(dirname "$0")"
source padel-env/bin/activate
streamlit run app.py