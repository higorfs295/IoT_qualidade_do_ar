#!/bin/bash
# Script de automação para ambiente Linux
sudo apt update && sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
