#!/bin/bash

# Update apt packages
apt-get update

# Install Chromium along with its required dependencies
sudo apt-get install -y chromium-browser

# Python dependencies for the mcp to run
pip install -r requirements.txt
