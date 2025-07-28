#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo 'Edit .env with your config and run main.py'
