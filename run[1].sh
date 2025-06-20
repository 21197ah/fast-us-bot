#!/bin/bash
source ~/.bashrc
cd /root/fast-us-bot
export $(cat .env | xargs)
python3 main.py
